from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone  # Add this import
from .models import Category, Question, QuizSession, QuizAnswer
from .forms import QuestionForm
import random

@login_required
def start_quiz(request, category_id):
    """Start a new quiz session"""
    category = get_object_or_404(Category, id=category_id)
    questions = list(Question.objects.filter(category=category))
    
    if len(questions) < 5:
        messages.error(request, 'Not enough questions in this category. Please try another.')
        return redirect('dashboard:student_dashboard')
    
    # Select random 5 questions
    selected_questions = random.sample(questions, min(5, len(questions)))
    
    # Create quiz session
    session = QuizSession.objects.create(
        user=request.user,
        category=category
    )
    
    # Store question IDs in session
    request.session['current_quiz'] = {
        'session_id': session.id,
        'question_ids': [q.id for q in selected_questions],
        'current_index': 0,
        'score': 0
    }
    
    return redirect('quizzes:take_quiz')

@login_required
def take_quiz(request):
    """Take a quiz"""
    quiz_data = request.session.get('current_quiz')
    if not quiz_data:
        messages.error(request, 'No active quiz session found.')
        return redirect('dashboard:student_dashboard')
    
    question_ids = quiz_data['question_ids']
    current_index = quiz_data['current_index']
    
    if current_index >= len(question_ids):
        return redirect('quizzes:quiz_complete')
    
    question = get_object_or_404(Question, id=question_ids[current_index])
    
    context = {
        'question': question,
        'current_index': current_index + 1,
        'total_questions': len(question_ids),
        'progress': (current_index / len(question_ids)) * 100
    }
    
    return render(request, 'quizzes/take_quiz.html', context)

@login_required
def submit_answer(request):
    """Submit an answer for the current question"""
    if request.method == 'POST':
        question_id = request.POST.get('question_id')
        selected_answer = int(request.POST.get('answer'))
        
        question = get_object_or_404(Question, id=question_id)
        is_correct = (selected_answer == question.correct_answer)
        
        quiz_data = request.session.get('current_quiz')
        
        if quiz_data:
            # Update score
            if is_correct:
                quiz_data['score'] += 20
                request.session['current_quiz'] = quiz_data
            
            # Save answer to database
            session = QuizSession.objects.get(id=quiz_data['session_id'])
            QuizAnswer.objects.create(
                session=session,
                question=question,
                selected_answer=selected_answer,
                is_correct=is_correct
            )
        
        return JsonResponse({
            'correct': is_correct,
            'correct_answer': question.correct_answer,
            'score': quiz_data.get('score', 0) if quiz_data else 0
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def next_question(request):
    """Get the next question"""
    quiz_data = request.session.get('current_quiz')
    
    if quiz_data:
        quiz_data['current_index'] += 1
        request.session['current_quiz'] = quiz_data
        
        if quiz_data['current_index'] >= len(quiz_data['question_ids']):
            return JsonResponse({'completed': True})
        
        next_q_id = quiz_data['question_ids'][quiz_data['current_index']]
        next_q = get_object_or_404(Question, id=next_q_id)
        
        return JsonResponse({
            'completed': False,
            'question': {
                'id': next_q.id,
                'text': next_q.text,
                'options': next_q.get_options(),
                'current_index': quiz_data['current_index'] + 1,
                'total': len(quiz_data['question_ids']),
                'category': next_q.category.name
            }
        })
    
    return JsonResponse({'error': 'No quiz session'}, status=400)

@login_required
def quiz_complete(request):
    """Handle quiz completion"""
    quiz_data = request.session.get('current_quiz')
    
    if not quiz_data:
        messages.error(request, 'No active quiz session found.')
        return redirect('dashboard:student_dashboard')
    
    try:
        # Get the quiz session
        session = QuizSession.objects.get(id=quiz_data['session_id'])
        session.score = quiz_data['score']
        session.completed = True
        session.completed_at = timezone.now()  # Now timezone is imported
        session.save()
        
        # Update user points and level
        user = request.user
        user.points += quiz_data['score']
        user.save()
        user.update_level()  # This will save again if level changed
        
        # Record quiz completion
        user.total_quizzes_taken += 1
        user.total_correct_answers += quiz_data['score'] // 20
        user.last_active = timezone.now()
        user.save(update_fields=['total_quizzes_taken', 'total_correct_answers', 'last_active'])
        
        # Clear session data
        del request.session['current_quiz']
        
        # Show success message
        messages.success(
            request, 
            f'Quiz completed! You scored {quiz_data["score"]} points. '
            f'You are now at Level {user.level}!'
        )
        
        context = {
            'score': quiz_data['score'],
            'category': session.category.name,
            'total_possible': len(quiz_data['question_ids']) * 20,
            'percentage': (quiz_data['score'] / (len(quiz_data['question_ids']) * 20)) * 100,
            'new_level': user.level,
            'total_points': user.points,
            'question': session.answers.first().question if session.answers.exists() else None
        }
        
        return render(request, 'quizzes/quiz_complete.html', context)
        
    except QuizSession.DoesNotExist:
        messages.error(request, 'Quiz session not found.')
        return redirect('dashboard:student_dashboard')

# Admin views
@login_required
def manage_questions(request):
    """Manage questions (admin only)"""
    if request.user.role not in ['admin', 'teacher']:
        return redirect('dashboard:student_dashboard')
    
    questions = Question.objects.all().order_by('-created_at')
    categories = Category.objects.all()
    
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Question added successfully!')
            return redirect('quizzes:manage_questions')
    else:
        form = QuestionForm()
    
    context = {
        'questions': questions,
        'categories': categories,
        'form': form
    }
    
    return render(request, 'quizzes/manage_questions.html', context)

@login_required
def delete_question(request, question_id):
    """Delete a question (admin only)"""
    if request.user.role not in ['admin', 'teacher']:
        return redirect('dashboard:student_dashboard')
    
    question = get_object_or_404(Question, id=question_id)
    question.delete()
    messages.success(request, 'Question deleted successfully!')
    return redirect('quizzes:manage_questions')