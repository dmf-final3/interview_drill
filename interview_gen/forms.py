from django import forms
from .models import InterviewGen

class InterviewGenForm(forms.ModelForm):
    class Meta:

        model = InterviewGen

        fields = ['company_name', 'experience']

        labels = {
            'company_name': '지망회사',  # Company name을 '회사명'으로 변경
            'experience': '자기소개서'       # Experience를 '경험'으로 변경
        }

        # Placeholder 설정
        widgets = {
            'company_name': forms.TextInput(attrs={'placeholder': '회사명을 정확히 입력해주세요. (예: LG에너지솔루션)'}),
            'experience': forms.Textarea(attrs={'placeholder': '자기소개서의 일부, 혹은 전체를 복사 붙여넣기 해주세요.'})
        }