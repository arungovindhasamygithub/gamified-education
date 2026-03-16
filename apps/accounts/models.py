from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Administrator'),
    )
    
    LEVEL_CHOICES = (
        (1, 'Bronze'),
        (2, 'Silver'),
        (3, 'Gold'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    
    # --- UPDATED: ManyToManyField allows ONE student to have MULTIPLE teachers ---
    assigned_teachers = models.ManyToManyField(
        'self', 
        symmetrical=False,
        blank=True, 
        related_name='my_students',
        limit_choices_to={'role': 'teacher'},
        help_text="Master Admin: Assign this student to multiple teachers."
    )
    # ----------------------------------------------------------------------------

    school = models.CharField(max_length=100, blank=True)
    grade = models.CharField(max_length=50, blank=True)
    points = models.IntegerField(default=0)
    level = models.IntegerField(default=1, choices=LEVEL_CHOICES)
    total_quizzes_taken = models.IntegerField(default=0)
    total_correct_answers = models.IntegerField(default=0)
    last_active = models.DateTimeField(default=timezone.now)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    
    def __str__(self):
        return f"{self.username} - {self.get_role_display()} (Level {self.level})"
    
    def update_level(self):
        old_level = self.level
        if self.points >= 300:
            self.level = 3
        elif self.points >= 100:
            self.level = 2
        else:
            self.level = 1
        
        if old_level != self.level:
            self.save(update_fields=['level'])
            return True
        return False
    
    def add_points(self, points):
        self.points += points
        self.save(update_fields=['points'])
        self.update_level()
    
    def get_level_name(self):
        return dict(self.LEVEL_CHOICES).get(self.level, 'Bronze')
    
    def get_progress_to_next_level(self):
        if self.level == 1:
            return min(100, (self.points / 100) * 100)
        elif self.level == 2:
            return min(100, ((self.points - 100) / 200) * 100)
        else:
            return 100
    
    def record_quiz_completion(self, score, total_questions):
        self.total_quizzes_taken += 1
        self.total_correct_answers += score // 20
        self.last_active = timezone.now()
        self.save(update_fields=['total_quizzes_taken', 'total_correct_answers', 'last_active'])
    
    class Meta:
        ordering = ['-points', 'username']
        verbose_name = 'User'
        verbose_name_plural = 'Users'