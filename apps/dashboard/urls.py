from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('submit-mission/', views.submit_mission, name='submit_mission'),
    path('assign-quiz/', views.assign_quiz, name='assign_quiz'),
    path('assign-student/', views.assign_student_to_teacher, name='assign_student_to_teacher'),
   
]