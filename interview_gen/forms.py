from django import forms
from .models import InterviewGen

class InterviewGenForm(forms.ModelForm):
    class Meta:

        model = InterviewGen

        fields = ['company_name', 'experience']

        labels = {
            'company_name': '지망회사',  # Company name을 '회사명'으로 변경
            'experience': '관련경험'       # Experience를 '경험'으로 변경
        }

        # Placeholder 설정
        widgets = {
            'company_name': forms.TextInput(attrs={'placeholder': '회사명을 정확히 입력해주세요. (예: LG에너지솔루션)'}),
            'experience': forms.Textarea(attrs={'placeholder': '경험을 구체적으로 서술해주세요.'})
        }