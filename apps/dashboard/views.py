from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Avg, Count
from django.utils import timezone
from datetime import timedelta
from apps.accounts.models import User
from apps.quizzes.models import QuizSession, Category, Question, QuizAssignment
from .models import Mission, MissionSubmission
from .forms import MissionSubmissionForm
from .models import PhysicalEvent, EventSubmission
from .forms import EventSubmissionForm

# --- Helper function for permissions ---
def is_teacher(user):
    return user.is_authenticated and user.role in ['teacher', 'admin']


@login_required
def student_dashboard(request):
    """Student dashboard view"""
    if request.user.role != 'student':
        return redirect('dashboard:teacher_dashboard' if request.user.role == 'teacher' else 'dashboard:admin_dashboard')
    
    now = timezone.now()
    
    assigned_quizzes = QuizAssignment.objects.filter(
        student=request.user, 
        is_completed=False,
        expires_at__gt=now
    )
    assigned_category_ids = assigned_quizzes.values_list('category_id', flat=True)
    categories = Category.objects.filter(id__in=assigned_category_ids)
    
    leaderboard = User.objects.filter(role='student').order_by('-points')[:10]
    quiz_history = QuizSession.objects.filter(user=request.user, completed=True).order_by('-completed_at')[:5]
    
    active_mission = Mission.objects.filter(is_active=True).first()
    existing_submission = None
    if active_mission:
        existing_submission = MissionSubmission.objects.filter(
            user=request.user, 
            mission=active_mission
        ).first()
    
    context = {
        'categories': categories,
        'assigned_quizzes': assigned_quizzes,
        'leaderboard': leaderboard,
        'quiz_history': quiz_history,
        'active_mission': active_mission,
        'existing_submission': existing_submission
    }
    
    return render(request, 'dashboard/student_dashboard.html', context)


@login_required
@user_passes_test(is_teacher, login_url='/')
def teacher_dashboard(request):
    """Teacher dashboard with correct student_progress definition and Live Feed"""
    current_date = timezone.now()
    
    # 1. Get Students based on role 
    # FIXED: Changed assigned_teacher to assigned_teachers
    if request.user.role == 'teacher':
        students = User.objects.filter(role='student', assigned_teachers=request.user)
    else:
        students = User.objects.filter(role='student')

    total_students = students.count()
    avg_points = students.aggregate(Avg('points'))['points__avg'] or 0
    active_today = students.filter(last_active__date=current_date.date()).count()

    # 2. Define student_progress correctly
    student_progress = []
    for student in students.order_by('-points')[:20]:
        has_active = QuizAssignment.objects.filter(
            student=student, 
            is_completed=False, 
            expires_at__gt=current_date
        ).exists()

        student_progress.append({
            'id': student.id,
            'name': student.username,
            'level': student.level,
            'points': student.points,
            'has_active_assignment': has_active,
        })

    # 3. Get Active Assignments for the Live Feed at the bottom
    active_assignments = QuizAssignment.objects.filter(
        is_completed=False,
        expires_at__gt=current_date
    ).select_related('student', 'category').order_by('-expires_at')

    if request.user.role == 'teacher':
        active_assignments = active_assignments.filter(instructor=request.user)

    context = {
        'current_date': current_date,
        'total_students': total_students,
        'avg_points': avg_points,
        'active_today': active_today,
        'student_progress': student_progress,
        'active_assignments': active_assignments,
        'available_categories': Category.objects.all(),
    }
    return render(request, 'dashboard/teacher_dashboard.html', context)


@login_required
@user_passes_test(is_teacher, login_url='/')
def assign_quiz(request):
    """Handles multiple modules to multiple students"""
    if request.method == 'POST':
        quiz_ids = request.POST.getlist('quiz_id')  
        time_limit = request.POST.get('time_limit')
        student_ids = request.POST.getlist('student_ids')

        if not quiz_ids or not time_limit or not student_ids:
            messages.error(request, "Deployment Failed: Missing parameters.")
            return redirect('dashboard:teacher_dashboard')

        try:
            minutes = int(time_limit)
            expiration_time = timezone.now() + timedelta(minutes=minutes)
            
            # Determine target students
            target_students = User.objects.filter(role='student')
            if 'ALL' not in student_ids:
                target_students = target_students.filter(id__in=student_ids)
            
            if request.user.role == 'teacher':
                # FIXED: Changed assigned_teacher to assigned_teachers
                target_students = target_students.filter(assigned_teachers=request.user)

            # Assign each selected quiz to each selected student
            assigned_count = 0
            for q_id in quiz_ids:
                category = get_object_or_404(Category, id=q_id)
                for student in target_students:
                    QuizAssignment.objects.update_or_create(
                        student=student,
                        category=category,
                        defaults={
                            'instructor': request.user,
                            'expires_at': expiration_time,
                            'is_completed': False
                        }
                    )
                    assigned_count += 1

            messages.success(request, f"Successfully deployed {len(quiz_ids)} modules to {target_students.count()} operatives.")
        except Exception as e:
            messages.error(request, f"System Error: {str(e)}")

    return redirect('dashboard:teacher_dashboard')


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
    
    students_list = User.objects.filter(role='student').order_by('username')
    teachers_list = User.objects.filter(role='teacher').order_by('username')
    
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
        'categories': categories,
        'students_list': students_list, 
        'teachers_list': teachers_list  
    }
    
    return render(request, 'dashboard/admin_dashboard.html', context)


@login_required
def assign_student_to_teacher(request):
    """Handles multiple assignments and unassigning (removing) students"""
    if request.user.role != 'admin':
        messages.error(request, 'Access Denied: Only Master Admins can assign students.')
        return redirect('dashboard:student_dashboard')

    if request.method == 'POST':
        student_ids = request.POST.getlist('student_ids') 
        single_student_id = request.POST.get('student_id')
        teacher_id = request.POST.get('teacher_id')
        action = request.POST.get('action', 'assign')

        target_ids = student_ids if student_ids else ([single_student_id] if single_student_id else [])

        if not target_ids:
            messages.error(request, 'Deployment Failed: No operatives selected.')
            return redirect('dashboard:admin_dashboard')

        try:
            students = User.objects.filter(id__in=target_ids, role='student')
            
            # FIXED: Uses ManyToMany .add() and .remove() logic!
            if action == 'remove' and teacher_id:
                teacher = get_object_or_404(User, id=teacher_id, role='teacher')
                for student in students:
                    student.assigned_teachers.remove(teacher)
                messages.success(request, f"Students removed from {teacher.username}'s roster.")
                
            elif teacher_id:
                teacher = get_object_or_404(User, id=teacher_id, role='teacher')
                for student in students:
                    student.assigned_teachers.add(teacher)
                messages.success(request, f"Students assigned to {teacher.username}.")
            else:
                messages.error(request, "Please select an instructor.")
                
        except Exception as e:
            messages.error(request, f"System Error: {str(e)}")

    return redirect('dashboard:admin_dashboard')


@login_required
def submit_mission(request):
    """Submit a mission"""
    if request.method == 'POST':
        mission_id = request.POST.get('mission_id')
        mission = get_object_or_404(Mission, id=mission_id)
        
        existing = MissionSubmission.objects.filter(user=request.user, mission=mission).first()
        if existing:
            messages.error(request, 'You have already submitted this mission.')
            return redirect('dashboard:student_dashboard')
        
        form = MissionSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.user = request.user
            submission.mission = mission
            submission.submitted_at = timezone.now()
            submission.save()
            
            messages.success(request, 'Mission submitted successfully! Awaiting review.')
        else:
            messages.error(request, 'Error submitting mission.')
    
    return redirect('dashboard:student_dashboard')


def student_physical_events(request):
    events = PhysicalEvent.objects.all()
    
    if request.method == 'POST':
        event_id = request.POST.get('event_id')
        event = get_object_or_404(PhysicalEvent, id=event_id)
        form = EventSubmissionForm(request.POST, request.FILES) # request.FILES is required for images!
        
        if form.is_valid():
            submission = form.save(commit=False)
            submission.student = request.user
            submission.event = event
            submission.save()
            messages.success(request, "Image uploaded successfully! Waiting for admin approval.")
            return redirect('dashboard:student_physical_events')
            
    else:
        form = EventSubmissionForm()
        
    return render(request, 'dashboard/student_events.html', {'events': events, 'form': form})

# --- FOR ADMIN/TEACHER: View uploaded photos and grade them ---
def grade_physical_events(request):
    # Get all submissions that haven't been graded yet
    pending_submissions = EventSubmission.objects.filter(status='pending').order_by('-submitted_at')
    
    if request.method == 'POST':
        submission_id = request.POST.get('submission_id')
        action = request.POST.get('action')
        submission = get_object_or_404(EventSubmission, id=submission_id)
        
        if action == 'approve':
            points = int(request.POST.get('points', submission.event.max_points))
            submission.status = 'approved'
            submission.points_awarded = points
            submission.save()
            
            # Give points to the student using your existing add_points method
            submission.student.add_points(points) 
            messages.success(request, f"Approved! {points} XP awarded to {submission.student.username}.")
            
        elif action == 'reject':
            submission.status = 'rejected'
            submission.save()
            messages.error(request, f"Submission from {submission.student.username} rejected.")
            
        return redirect('dashboard:grade_physical_events')
        
    return render(request, 'dashboard/admin_grade_events.html', {'submissions': pending_submissions})


