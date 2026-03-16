from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from .models import User

class CustomUserAdmin(UserAdmin):
    # Change 'actions' to 'custom_actions' to avoid conflict
    list_display = ('username', 'email', 'role', 'school', 'grade', 'points', 'level', 'colored_status', 'date_joined', 'action_buttons')
    list_filter = ('role', 'level', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'school')
    ordering = ('-date_joined',)
    
    # Change from 'actions' to 'custom_actions' (this was the problem)
    custom_actions = ['reset_points', 'set_level_one', 'make_student', 'make_teacher', 'export_users']
    
    # Django's built-in actions attribute - use this instead
    actions = ['reset_points', 'set_level_one', 'make_student', 'make_teacher', 'export_users']
    
    list_display_links = ('username', 'email')
    
    fieldsets = UserAdmin.fieldsets + (
        ('EcoQuest Profile', {
            'fields': ('role', 'school', 'grade', 'points', 'level'),
            'classes': ('wide', 'collapse'),
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('EcoQuest Profile', {
            'fields': ('role', 'school', 'grade', 'points', 'level'),
        }),
    )
    
    def colored_status(self, obj):
        """Color code user status"""
        if obj.is_active:
            return format_html('<span style="color: green; font-weight: bold;">✓ Active</span>')
        return format_html('<span style="color: red; font-weight: bold;">✗ Inactive</span>')
    colored_status.short_description = 'Status'
    colored_status.admin_order_field = 'is_active'
    
    def action_buttons(self, obj):
        """Add action buttons for each user"""
        return format_html(
            '<a class="button" href="{}" style="background: #52b788; color: white; padding: 3px 8px; border-radius: 4px; text-decoration: none; margin-right: 5px;">Edit</a>'
            '<a class="button" href="{}" style="background: #e07a5f; color: white; padding: 3px 8px; border-radius: 4px; text-decoration: none;">View</a>',
            reverse('admin:accounts_user_change', args=[obj.id]),
            reverse('admin:accounts_user_change', args=[obj.id])
        )
    action_buttons.short_description = 'Actions'
    
    def reset_points(self, request, queryset):
        """Reset points for selected users"""
        updated = queryset.update(points=0, level=1)
        self.message_user(request, f'{updated} users had their points reset to 0.')
    reset_points.short_description = "Reset points to 0"
    
    def set_level_one(self, request, queryset):
        """Set level to 1 for selected users"""
        updated = queryset.update(level=1)
        self.message_user(request, f'{updated} users set to Level 1.')
    set_level_one.short_description = "Set level to 1"
    
    def make_student(self, request, queryset):
        """Change role to student"""
        updated = queryset.update(role='student')
        self.message_user(request, f'{updated} users changed to Student role.')
    make_student.short_description = "Change role to Student"
    
    def make_teacher(self, request, queryset):
        """Change role to teacher"""
        updated = queryset.update(role='teacher')
        self.message_user(request, f'{updated} users changed to Teacher role.')
    make_teacher.short_description = "Change role to Teacher"
    
    def export_users(self, request, queryset):
        """Export users as CSV"""
        import csv
        from django.http import HttpResponse
        from datetime import datetime
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="users_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Username', 'Email', 'Role', 'School', 'Grade', 'Points', 'Level', 'Joined Date', 'Last Login'])
        
        for user in queryset:
            writer.writerow([
                user.username,
                user.email,
                user.role,
                user.school,
                user.grade,
                user.points,
                user.level,
                user.date_joined.strftime("%Y-%m-%d %H:%M"),
                user.last_login.strftime("%Y-%m-%d %H:%M") if user.last_login else 'Never'
            ])
        
        return response
    export_users.short_description = "Export selected users to CSV"