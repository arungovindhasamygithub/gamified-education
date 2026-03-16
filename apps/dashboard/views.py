from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Avg, Count
from django.utils import timezone
from datetime import timedelta
from apps.accounts.models import User
from apps.quizzes.models import QuizSession, Category, Question  # Added Question import
from .models import Mission, MissionSubmission
from .forms import MissionSubmissionForm

@login_required
def student_dashboard(request):
    """Student dashboard view"""
    if request.user.role != 'student':
        return redirect('dashboard:teacher_dashboard' if request.user.role == 'teacher' else 'dashboard:admin_dashboard')
    
    categories = Category.objects.all()
    
    # Get leaderboard
    leaderboard = User.objects.filter(role='student').order_by('-points')[:10]
    
    # Get user's quiz history
    quiz_history = QuizSession.objects.filter(user=request.user, completed=True).order_by('-completed_at')[:5]
    
    # Get active mission
    active_mission = Mission.objects.filter(is_active=True).first()
    existing_submission = None
    if active_mission:
        existing_submission = MissionSubmission.objects.filter(
            user=request.user, 
            mission=active_mission
        ).first()
    
    context = {
        'categories': categories,
        'leaderboard': leaderboard,
        'quiz_history': quiz_history,
        'active_mission': active_mission,
        'existing_submission': existing_submission
    }
    
    return render(request, 'dashboard/student_dashboard.html', context)

@login_required
def teacher_dashboard(request):
    """Teacher dashboard view"""
    if request.user.role not in ['teacher', 'admin']:
        return redirect('dashboard:student_dashboard')
    
    # Get current date for display
    current_date = timezone.now()
    
    # Calculate date ranges
    today = timezone.now().date()
    
    # Get all students
    students = User.objects.filter(role='student')
    total_students = students.count()
    avg_points = students.aggregate(Avg('points'))['points__avg'] or 0
    
    # Get total completed quizzes
    total_quizzes = QuizSession.objects.filter(completed=True).count()
    
    # Get active students today
    active_today = User.objects.filter(
        role='student',
        last_active__date=today
    ).count()
    
    # Student progress data with more details
    student_progress = []
    for student in students.order_by('-points')[:20]:  # Top 20 students
        last_quiz = QuizSession.objects.filter(
            user=student, 
            completed=True
        ).order_by('-completed_at').first()
        
        # Determine tier
        if student.points >= 300:
            tier = 'Gold'
        elif student.points >= 100:
            tier = 'Silver'
        else:
            tier = 'Bronze'
        
        # Calculate progress to next level
        if student.level == 1:
            progress = min(100, (student.points / 100) * 100)
        elif student.level == 2:
            progress = min(100, ((student.points - 100) / 200) * 100)
        else:
            progress = 100
        
        student_progress.append({
            'name': student.username,
            'level': student.level,
            'points': student.points,
            'tier': tier,
            'last_active': student.last_active,
            'progress': round(progress, 1),
            'quizzes_taken': student.total_quizzes_taken,
            'correct_answers': student.total_correct_answers
        })
    
    # Recent activities - FIXED: Handle None values properly
    recent_activities = []
    
    # Add recent quiz completions
    recent_quizzes = QuizSession.objects.filter(
        completed=True,
        completed_at__isnull=False  # Only get quizzes with completion time
    ).select_related('user', 'category').order_by('-completed_at')[:5]
    
    for quiz in recent_quizzes:
        if quiz.completed_at:  # Safety check
            recent_activities.append({
                'type': 'quiz',
                'description': f"{quiz.user.username} completed {quiz.category.name} quiz",
                'time': quiz.completed_at,
                'icon': '📝'
            })
    
    # Add recent mission submissions
    recent_submissions = MissionSubmission.objects.filter(
        submitted_at__isnull=False  # Only get submissions with time
    ).select_related('user', 'mission').order_by('-submitted_at')[:5]
    
    for submission in recent_submissions:
        if submission.submitted_at:  # Safety check
            recent_activities.append({
                'type': 'mission',
                'description': f"{submission.user.username} submitted {submission.mission.title} mission",
                'time': submission.submitted_at,
                'icon': '🎯'
            })
    
    # Add new user registrations
    recent_users = User.objects.filter(
        date_joined__isnull=False
    ).order_by('-date_joined')[:3]
    
    for user in recent_users:
        if user.date_joined:  # Safety check
            recent_activities.append({
                'type': 'user',
                'description': f"{user.username} joined as {user.get_role_display()}",
                'time': user.date_joined,
                'icon': '👤'
            })
    
    # Filter out any activities with None time and sort
    recent_activities = [a for a in recent_activities if a['time'] is not None]
    
    # Sort activities by time (most recent first)
    try:
        recent_activities.sort(key=lambda x: x['time'], reverse=True)
    except TypeError:
        # If there's still a type error, manually sort
        recent_activities = sorted(
            [a for a in recent_activities if a['time'] is not None],
            key=lambda x: x['time'] if x['time'] else timezone.datetime.min,
            reverse=True
        )
    
    context = {
        'current_date': current_date,
        'total_students': total_students,
        'avg_points': avg_points,
        'total_quizzes': total_quizzes,
        'active_today': active_today,
        'student_progress': student_progress,
        'recent_activities': recent_activities[:10],  # Limit to 10 activities
    }
    
    return render(request, 'dashboard/teacher_dashboard.html', context)

@login_required
def admin_dashboard(request):
    """Admin dashboard view"""
    if request.user.role != 'admin':
        return redirect('dashboard:student_dashboard' if request.user.role == 'student' else 'dashboard:teacher_dashboard')
    
    total_students = User.objects.filter(role='student').count()
    total_teachers = User.objects.filter(role='teacher').count()
    total_categories = Category.objects.count()
    total_questions = Question.objects.count()
    total_quizzes = QuizSession.objects.filter(completed=True).count()
    pending_submissions = MissionSubmission.objects.filter(status='pending').count()
    
    users = User.objects.all().order_by('-date_joined')[:20]
    categories = Category.objects.all()
    
    context = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_categories': total_categories,
        'total_questions': total_questions,
        'total_quizzes': total_quizzes,
        'pending_submissions': pending_submissions,
        'users': users,
        'categories': categories
    }
    
    return render(request, 'dashboard/admin_dashboard.html', context)

@login_required
def submit_mission(request):
    """Submit a mission"""
    if request.method == 'POST':
        mission_id = request.POST.get('mission_id')
        mission = get_object_or_404(Mission, id=mission_id)
        
        # Check if already submitted
        existing = MissionSubmission.objects.filter(user=request.user, mission=mission).first()
        if existing:
            messages.error(request, 'You have already submitted this mission.')
            return redirect('dashboard:student_dashboard')
        
        form = MissionSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.user = request.user
            submission.mission = mission
            submission.submitted_at = timezone.now()  # Explicitly set submission time
            submission.save()
            
            messages.success(request, 'Mission submitted successfully! Awaiting review.')
        else:
            messages.error(request, 'Error submitting mission.')
    
    return redirect('dashboard:student_dashboard')