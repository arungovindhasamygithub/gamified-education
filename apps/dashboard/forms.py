from django import forms
from .models import MissionSubmission

class MissionSubmissionForm(forms.ModelForm):
    class Meta:
        model = MissionSubmission
        fields = ['image']
        widgets = {
            'image': forms.FileInput(attrs={'accept': 'image/*'})
        }