from django import forms
from .models import InterviewGen

class InterviewGenForm(forms.ModelForm):
    class Meta:
        model = InterviewGen
        fields = ['company_name', 'experience']