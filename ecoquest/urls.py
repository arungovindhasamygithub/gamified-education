"""
URL configuration for ecoquest project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.accounts import views as accounts_views

# Import admin classes
from apps.accounts.admin import CustomUserAdmin
from apps.quizzes.admin import CategoryAdmin, QuestionAdmin, QuizSessionAdmin, QuizAnswerAdmin
from apps.dashboard.admin import MissionAdmin, MissionSubmissionAdmin

# Import models
from apps.accounts.models import User
from apps.quizzes.models import Category, Question, QuizSession, QuizAnswer
from apps.dashboard.models import Mission, MissionSubmission

# Custom admin site
class EcoQuestAdminSite(admin.AdminSite):
    site_header = 'EcoQuest Administration'
    site_title = 'EcoQuest Admin Portal'
    index_title = 'Dashboard'
    site_url = '/dashboard/student/'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.admin_dashboard), name='admin_dashboard'),
            path('stats/', self.admin_view(self.stats_view), name='admin_stats'),
        ]
        return custom_urls + urls
    
    def admin_dashboard(self, request):
        """Custom admin dashboard view"""
        from django.shortcuts import render
        from django.db.models import Count, Sum
        
        context = {
            'total_users': User.objects.count(),
            'total_students': User.objects.filter(role='student').count(),
            'total_teachers': User.objects.filter(role='teacher').count(),
            'total_admins': User.objects.filter(role='admin').count(),
            'total_categories': Category.objects.count(),
            'total_questions': Question.objects.count(),
            'total_quizzes': QuizSession.objects.filter(completed=True).count(),
            'pending_submissions': MissionSubmission.objects.filter(status='pending').count(),
            'approved_submissions': MissionSubmission.objects.filter(status='approved').count(),
            
            'recent_users': User.objects.order_by('-date_joined')[:10],
            'recent_quizzes': QuizSession.objects.filter(completed=True).select_related('user', 'category').order_by('-completed_at')[:10],
            'pending_reviews': MissionSubmission.objects.filter(status='pending').select_related('user', 'mission').order_by('-submitted_at')[:10],
        }
        
        return render(request, 'admin/dashboard.html', context)
    
    def stats_view(self, request):
        """Statistics view"""
        from django.shortcuts import render
        from django.db.models import Count, Avg
        from django.utils import timezone
        from datetime import timedelta
        
        # Last 30 days stats
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        context = {
            'new_users_30d': User.objects.filter(date_joined__gte=thirty_days_ago).count(),
            'quizzes_30d': QuizSession.objects.filter(completed_at__gte=thirty_days_ago).count(),
            'avg_score': QuizSession.objects.filter(completed=True).aggregate(Avg('score'))['score__avg'] or 0,
            
            'users_by_role': User.objects.values('role').annotate(count=Count('id')),
            'quizzes_by_category': QuizSession.objects.filter(completed=True).values('category__name').annotate(count=Count('id')),
            'submissions_by_status': MissionSubmission.objects.values('status').annotate(count=Count('id')),
        }
        
        return render(request, 'admin/stats.html', context)

# Create custom admin site instance
custom_admin_site = EcoQuestAdminSite(name='ecoquest_admin')

# Register all models with custom admin site
custom_admin_site.register(User, CustomUserAdmin)
custom_admin_site.register(Category, CategoryAdmin)
custom_admin_site.register(Question, QuestionAdmin)
custom_admin_site.register(QuizSession, QuizSessionAdmin)
custom_admin_site.register(QuizAnswer, QuizAnswerAdmin)
custom_admin_site.register(Mission, MissionAdmin)
custom_admin_site.register(MissionSubmission, MissionSubmissionAdmin)

# URL Patterns
urlpatterns = [
    # Use custom admin site
    path('admin/', custom_admin_site.urls),
    
    # Home page
    path('', accounts_views.index_view, name='index'),
    
    # Authentication
    path('accounts/', include('apps.accounts.urls')),
    
    # App URLs
    path('quizzes/', include('apps.quizzes.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
]

# Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)