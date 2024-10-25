from django.shortcuts import render, redirect
from .models import InterviewGen
from .forms import InterviewGenForm

# Create your views here.
def index(request):
    form = InterviewGenForm()
    context = {
        'form' : form,
    }
    return render(request, 'form.html', context)


def create(request):
    if request.method == 'POST':
        form = InterviewGenForm(request.POST)
        if form.is_valid():
            # 폼 데이터가 유효하면 저장
            form.save()
            return redirect('form.html')  # 저장 후 리디렉션 (예: 성공 페이지)
    else:
        form = InterviewGenForm()  # GET 요청일 때 빈 폼 표시
    
    context = {
        'form': form,
    }
    return render(request, 'form.html', context)