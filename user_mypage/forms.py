from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Mypage
from django import forms


class MypageSignUpForm(UserCreationForm):
    username = forms.CharField(
        label="사용자 이름",
        widget=forms.TextInput(attrs={'placeholder': '사용자 이름'})  # placeholder를 레이블과 동일하게 설정
    )
    email = forms.EmailField(
        label="이메일 주소",
        widget=forms.EmailInput(attrs={'placeholder': '이메일 주소'})  # placeholder 설정
    )
    major = forms.CharField(
        label="전공",
        widget=forms.TextInput(attrs={'placeholder': '전공'})  # placeholder 설정
    )
    desired_job = forms.CharField(
        label="희망 직무",
        widget=forms.TextInput(attrs={'placeholder': '희망 직무'})  # placeholder 설정
    )

    password1 = forms.CharField(
        label="비밀번호",
        widget=forms.PasswordInput(attrs={'placeholder': '비밀번호'}),
        help_text="""
        <ul style="list-style-type: disc; padding-left: 1rem; margin: 0;">
            <li style="margin: 0;">비밀번호는 다른 개인정보와 너무 유사하지 않아야 합니다.</li>
            <li style="margin: 0;">비밀번호는 최소 8자 이상이어야 합니다.</li>
            <li style="margin: 0;">비밀번호는 일반적으로 많이 사용되는 비밀번호가 아니어야 합니다.</li>
            <li style="margin: 0;">비밀번호는 숫자로만 이루어져 있으면 안 됩니다.</li>
        </ul>
        """
    )

    password2 = forms.CharField(
    label="비밀번호 확인",
    widget=forms.PasswordInput(attrs={'placeholder': '비밀번호 확인'}),
    help_text="""
    <ul style="list-style-type: disc; padding-left: 1rem; margin: 0;">
        <li style="margin: 0;">확인을 위해 이전과 동일한 비밀번호를 입력하세요.</li>
    </ul>
    """
    )

    class Meta():
        model = Mypage
        fields = ('username', 'email', 'major', 'desired_job', 'password1', 'password2')


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="아이디",  # Username을 "아이디"로 변경
        widget=forms.TextInput(attrs={'placeholder': '아이디'})
    )
    password = forms.CharField(
        label="비밀번호",  # Password를 "비밀번호"로 변경
        widget=forms.PasswordInput(attrs={'placeholder': '비밀번호'})
    )   