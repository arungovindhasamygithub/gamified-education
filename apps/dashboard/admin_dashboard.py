from django.contrib import admin
from django.shortcuts import render
from django.urls import path
from apps.accounts.models import User
from apps.quizzes.models import QuizSession, Category
from apps.dashboard.models import MissionSubmission

class AdminDashboardView:
    def get_admin_dashboard(self, request):
        """Custom admin dashboard view"""
        context = {
            'total_users': User.objects.count(),
            'total_students': User.objects.filter(role='student').count(),
            'total_teachers': User.objects.filter(role='teacher').count(),
            'total_admins': User.objects.filter(role='admin').count(),
            'total_categories': Category.objects.count(),
            'total_quizzes': QuizSession.objects.filter(completed=True).count(),
            'pending_submissions': MissionSubmission.objects.filter(status='pending').count(),
            
            'recent_users': User.objects.order_by('-date_joined')[:10],
            'recent_quizzes': QuizSession.objects.filter(completed=True).select_related('user', 'category').order_by('-completed_at')[:10],
            'pending_reviews': MissionSubmission.objects.filter(status='pending').select_related('user', 'mission').order_by('-submitted_at')[:10],
            
            'stats': {
                'users_by_role': User.objects.values('role').annotate(count=models.Count('id')),
                'quizzes_by_category': QuizSession.objects.filter(completed=True).values('category__name').annotate(count=models.Count('id')),
            }
        }
        
        return render(request, 'admin/dashboard.html', context)