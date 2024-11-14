from django.shortcuts import render, redirect, get_object_or_404
from .forms import MypageSignUpForm, CustomAuthenticationForm
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from interview_gen.models import InterviewGen
from .models import Mypage
from django.contrib.auth.views import LoginView

class CustomLoginView(LoginView):
    form_class = CustomAuthenticationForm  # 한글 레이블이 적용된 폼 사용
    template_name = 'user_mypage/login.html'

# Create your views here.
def signup(request):
    if request.method == 'POST':
        form = MypageSignUpForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('user_mypage:login')

    else:
        form = MypageSignUpForm()

    context = {
        'form': form,
    }

    return render(request, 'signup.html', context)


def login(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('interview_gen:index')

    else:
        form = CustomAuthenticationForm()
    
    context = {
        'form': form,
    }

    return render(request, 'login.html', context)

    

def logout(request):
    auth_logout(request)
    return redirect('interview_gen:index')


@login_required
def history(request):
    # 현재 로그인한 사용자의 ID를 사용하여 InterviewGen 객체들을 조회
    user_interviews = InterviewGen.objects.filter(user=request.user)

    # 조회된 데이터를 템플릿에 전달
    context = {
        'major': request.user.major,  # 'user' 대신 'request.user' 사용
        'desired_job': request.user.desired_job,  # 'user' 대신 'request.user' 사용
        'interviews': user_interviews
    }
    return render(request, 'mypage.html', context)


@login_required
def detail(request, pk):
    interview = get_object_or_404(InterviewGen, pk=pk)
    return render(request, 'detail.html', {'interview': interview})