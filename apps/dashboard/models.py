from django.db import models
from django.conf import settings
from apps.accounts.models import User

class Mission(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    points_reward = models.IntegerField(default=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class MissionSubmission(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submissions')
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='missions/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.mission.title}"
    
# 1. The Event created by the Admin/Teacher
class PhysicalEvent(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    max_points = models.IntegerField(default=100) # Points student gets for doing it

    def __str__(self):
        return self.title

# 2. The Image uploaded by the Student
class EventSubmission(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Verification'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(PhysicalEvent, on_delete=models.CASCADE)
    proof_image = models.ImageField(upload_to='physical_events/') # Saves to your media folder
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    points_awarded = models.IntegerField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - {self.event.title}"