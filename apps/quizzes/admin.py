from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from django.urls import reverse, path
from django.http import HttpResponse
from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
import csv
import io
from .models import Category, Question, QuizSession, QuizAnswer

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = ['text', 'option1', 'option2', 'option3', 'option4', 'correct_answer']
    show_change_link = True

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'question_count', 'created_at']
    search_fields = ['name', 'description']
    list_filter = ['created_at']
    inlines = [QuestionInline]
    
    def question_count(self, obj):
        """Display number of questions in category"""
        count = obj.questions.count()
        return format_html(
            '<span style="background: {}; padding: 3px 10px; border-radius: 12px; color: white;">{} question{}</span>',
            '#2d6a4f' if count > 0 else '#666',
            str(count),
            's' if count != 1 else ''
        )
    question_count.short_description = 'Questions'
    question_count.admin_order_field = 'questions__count'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(questions_count=Count('questions'))

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['id', 'category', 'short_text', 'correct_answer_display', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['text', 'category__name']
    list_editable = ['category']
    list_per_page = 20
    list_select_related = ['category']
    
    # Only import action - no export
    actions = ['import_questions_from_csv']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'text'),
            'classes': ('wide',)
        }),
        ('Answer Options', {
            'fields': ('option1', 'option2', 'option3', 'option4'),
            'classes': ('wide',)
        }),
        ('Correct Answer', {
            'fields': ('correct_answer',),
            'classes': ('wide',)
        }),
    )
    
    def short_text(self, obj):
        """Truncate long question text"""
        return obj.text[:75] + '...' if len(obj.text) > 75 else obj.text
    short_text.short_description = 'Question'
    
    def correct_answer_display(self, obj):
        """Display correct answer with highlighting"""
        options = [obj.option1, obj.option2, obj.option3, obj.option4]
        correct = options[obj.correct_answer]
        return format_html(
            '<span style="background: #2a9d8f; color: white; padding: 3px 8px; border-radius: 4px;">✓ {}</span>',
            correct[:50] + '...' if len(correct) > 50 else correct
        )
    correct_answer_display.short_description = 'Correct Answer'
    
    def import_questions_from_csv(self, request, queryset):
        """
        Import questions from CSV file - direct admin action
        """
        if 'apply' in request.POST:
            # Handle the CSV file upload
            csv_file = request.FILES.get('csv_file')
            if not csv_file:
                self.message_user(request, "Please select a CSV file to import.", level='ERROR')
                return redirect(request.get_full_path())
            
            if not csv_file.name.endswith('.csv'):
                self.message_user(request, "File must be a CSV.", level='ERROR')
                return redirect(request.get_full_path())
            
            try:
                # Read and parse CSV
                decoded_file = csv_file.read().decode('utf-8')
                io_string = io.StringIO(decoded_file)
                reader = csv.DictReader(io_string)
                
                # Check if CSV has required columns
                required_columns = ['Category', 'Question Text', 'Option 1', 'Option 2', 'Option 3', 'Option 4', 'Correct Answer']
                if not all(col in reader.fieldnames for col in required_columns):
                    self.message_user(
                        request, 
                        f"CSV must contain these columns: {', '.join(required_columns)}", 
                        level='ERROR'
                    )
                    return redirect(request.get_full_path())
                
                # Import questions
                imported = 0
                errors = []
                
                for row_num, row in enumerate(reader, start=2):
                    try:
                        # Get or create category
                        category_name = row.get('Category', '').strip()
                        if not category_name:
                            category_name = 'General'
                        
                        category, _ = Category.objects.get_or_create(name=category_name)
                        
                        # Create question
                        question = Question(
                            category=category,
                            text=row.get('Question Text', '').strip(),
                            option1=row.get('Option 1', '').strip(),
                            option2=row.get('Option 2', '').strip(),
                            option3=row.get('Option 3', '').strip(),
                            option4=row.get('Option 4', '').strip(),
                            correct_answer=int(row.get('Correct Answer', 0))
                        )
                        question.save()
                        imported += 1
                        
                    except Exception as e:
                        errors.append(f"Row {row_num}: {str(e)}")
                
                # Show results
                if errors:
                    self.message_user(
                        request, 
                        f"Imported {imported} questions. Errors: {'; '.join(errors[:5])}", 
                        level='WARNING'
                    )
                else:
                    self.message_user(request, f"Successfully imported {imported} questions.")
                
            except Exception as e:
                self.message_user(request, f"Error reading CSV file: {str(e)}", level='ERROR')
            
            return redirect(request.get_full_path())
        
        # Show the import form
        context = {
            'title': 'Import Questions from CSV',
            'action': 'import_questions_from_csv',
            'queryset': queryset,
            'opts': self.model._meta,
        }
        return TemplateResponse(request, 'admin/quizzes/csv_import_form.html', context)
    
    import_questions_from_csv.short_description = "📥 Import questions from CSV"

@admin.register(QuizSession)
class QuizSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'category', 'score', 'completed', 'started_at']
    list_filter = ['completed', 'category']
    search_fields = ['user__username', 'category__name']
    readonly_fields = ['started_at', 'completed_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'category')

@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'question', 'is_correct']
    list_filter = ['is_correct']
    search_fields = ['session__user__username', 'question__text']