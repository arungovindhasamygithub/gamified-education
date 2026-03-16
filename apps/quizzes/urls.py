from django.urls import path
from . import views

app_name = 'quizzes'

urlpatterns = [
    path('start/<int:category_id>/', views.start_quiz, name='start_quiz'),
    path('take/', views.take_quiz, name='take_quiz'),
    path('submit-answer/', views.submit_answer, name='submit_answer'),
    path('next-question/', views.next_question, name='next_question'),
    path('complete/', views.quiz_complete, name='quiz_complete'),
    
    # Admin
    path('manage/', views.manage_questions, name='manage_questions'),
    path('delete/<int:question_id>/', views.delete_question, name='delete_question'),
]