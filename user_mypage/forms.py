from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Mypage

class MypageSignUpForm(UserCreationForm):
    class Meta():
        model = Mypage
        fields = ('username', 'email', 'major', 'desired_job', 'password1', 'password2')


class CustomAuthenticationForm(AuthenticationForm):
    pass