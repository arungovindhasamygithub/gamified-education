from django import forms
from .models import MissionSubmission
from .models import EventSubmission, PhysicalEvent

class MissionSubmissionForm(forms.ModelForm):
    class Meta:
        model = MissionSubmission
        fields = ['image']
        widgets = {
            'image': forms.FileInput(attrs={'accept': 'image/*'})
        }


class EventSubmissionForm(forms.ModelForm):
    class Meta:
        model = EventSubmission
        fields = ['proof_image']
        widgets = {
            'proof_image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
        }

class PhysicalEventForm(forms.ModelForm):
    class Meta:
        model = PhysicalEvent
        fields = ['title', 'description', 'max_points']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control border-2 py-2', 'placeholder': 'e.g. Park Cleanup Operation'}),
            'description': forms.Textarea(attrs={'class': 'form-control border-2', 'rows': 4, 'placeholder': 'Describe the mission objectives...'}),
            'max_points': forms.NumberInput(attrs={'class': 'form-control border-2 py-2', 'placeholder': '100'}),
        }