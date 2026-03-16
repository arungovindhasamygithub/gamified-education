
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Sum
from .models import Mission, MissionSubmission

class MissionSubmissionInline(admin.TabularInline):
    model = MissionSubmission
    extra = 0
    readonly_fields = ['user', 'image_preview', 'submitted_at', 'status']
    fields = ['user', 'image_preview', 'status', 'feedback', 'submitted_at']
    can_delete = False
    show_change_link = True
    
    def image_preview(self, obj):
        """Show image preview"""
        if obj.image:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="max-height: 50px; border-radius: 4px;" /></a>',
                obj.image.url,
                obj.image.url
            )
        return "No image"
    image_preview.short_description = 'Preview'

@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    list_display = ['title', 'points_reward', 'is_active', 'submission_count', 'created_at', 'status_badge']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description']
    list_editable = ['is_active']
    inlines = [MissionSubmissionInline]
    actions = ['activate_missions', 'deactivate_missions']
    
    fieldsets = (
        ('Mission Details', {
            'fields': ('title', 'description', 'points_reward')
        }),
        ('Status', {
            'fields': ('is_active',),
            'classes': ('wide',)
        }),
    )
    
    def submission_count(self, obj):
        """Count submissions for this mission"""
        count = obj.missionsubmission_set.count()
        approved = obj.missionsubmission_set.filter(status='approved').count()
        pending = obj.missionsubmission_set.filter(status='pending').count()
        
        return format_html(
            '<span style="background: #52b788; color: white; padding: 2px 6px; border-radius: 4px;">{}</span> total<br>'
            '<span style="color: #2a9d8f;">✓ {} approved</span><br>'
            '<span style="color: #f39c12;">⏳ {} pending</span>',
            count,
            approved,
            pending
        )
    submission_count.short_description = 'Submissions'
    
    def status_badge(self, obj):
        """Show status badge"""
        if obj.is_active:
            return format_html('<span style="background: #2a9d8f; color: white; padding: 4px 10px; border-radius: 12px;">✓ Active</span>')
        return format_html('<span style="background: #999; color: white; padding: 4px 10px; border-radius: 12px;">✗ Inactive</span>')
    status_badge.short_description = 'Status'
    
    def activate_missions(self, request, queryset):
        """Activate selected missions"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} missions activated.')
    activate_missions.short_description = "Activate selected missions"
    
    def deactivate_missions(self, request, queryset):
        """Deactivate selected missions"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} missions deactivated.')
    deactivate_missions.short_description = "Deactivate selected missions"

@admin.register(MissionSubmission)
class MissionSubmissionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_link', 'mission_link', 'image_thumbnail', 'status_colored', 'submitted_at', 'review_actions']
    list_filter = ['status', 'submitted_at', 'mission']
    search_fields = ['user__username', 'mission__title']
    list_per_page = 20
    actions = ['approve_submissions', 'reject_submissions', 'mark_as_pending']
    
    fieldsets = (
        ('Submission Information', {
            'fields': ('user', 'mission', 'image', 'status')
        }),
        ('Review', {
            'fields': ('feedback', 'reviewed_at'),
            'classes': ('wide',)
        }),
    )
    
    readonly_fields = ['image_preview', 'submitted_at', 'reviewed_at']
    
    def user_link(self, obj):
        """Link to user"""
        url = reverse('admin:accounts_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'
    
    def mission_link(self, obj):
        """Link to mission"""
        url = reverse('admin:dashboard_mission_change', args=[obj.mission.id])
        return format_html('<a href="{}">{}</a>', url, obj.mission.title)
    mission_link.short_description = 'Mission'
    
    def image_thumbnail(self, obj):
        """Show image thumbnail"""
        if obj.image:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="max-height: 40px; border-radius: 4px;" /></a>',
                obj.image.url,
                obj.image.url
            )
        return "No image"
    image_thumbnail.short_description = 'Evidence'
    
    def image_preview(self, obj):
        """Full image preview"""
        if obj.image:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="max-width: 300px; border-radius: 8px;" /></a>',
                obj.image.url,
                obj.image.url
            )
        return "No image uploaded"
    image_preview.short_description = 'Image Preview'
    
    def status_colored(self, obj):
        """Color-coded status"""
        colors = {
            'pending': ('#f39c12', '⏳ Pending'),
            'approved': ('#2a9d8f', '✓ Approved'),
            'rejected': ('#e63946', '✗ Rejected'),
        }
        color, text = colors.get(obj.status, ('#999', obj.status))
        return format_html('<span style="background: {}; color: white; padding: 4px 10px; border-radius: 12px;">{}</span>', color, text)
    status_colored.short_description = 'Status'
    
    def review_actions(self, obj):
        """Quick review actions"""
        if obj.status == 'pending':
            return format_html(
                '<a class="button" href="{}" style="background: #2a9d8f; color: white; padding: 4px 8px; border-radius: 4px; text-decoration: none; margin-right: 4px;">✓ Approve</a>'
                '<a class="button" href="{}" style="background: #e63946; color: white; padding: 4px 8px; border-radius: 4px; text-decoration: none;">✗ Reject</a>',
                f'/admin/dashboard/missionsubmission/{obj.id}/approve/',
                f'/admin/dashboard/missionsubmission/{obj.id}/reject/'
            )
        return "—"
    review_actions.short_description = 'Actions'
    
    def approve_submissions(self, request, queryset):
        """Approve selected submissions"""
        updated = queryset.update(status='approved', reviewed_at=admin.utils.timezone.now())
        self.message_user(request, f'{updated} submissions approved.')
    approve_submissions.short_description = "Approve selected submissions"
    
    def reject_submissions(self, request, queryset):
        """Reject selected submissions"""
        updated = queryset.update(status='rejected', reviewed_at=admin.utils.timezone.now())
        self.message_user(request, f'{updated} submissions rejected.')
    reject_submissions.short_description = "Reject selected submissions"
    
    def mark_as_pending(self, request, queryset):
        """Mark as pending"""
        updated = queryset.update(status='pending')
        self.message_user(request, f'{updated} submissions marked as pending.')
    mark_as_pending.short_description = "Mark as pending"
    
    def save_model(self, request, obj, form, change):
        """Auto-set reviewed_at when status changes"""
        if 'status' in form.changed_data:
            obj.reviewed_at = admin.utils.timezone.now()
        super().save_model(request, obj, form, change)