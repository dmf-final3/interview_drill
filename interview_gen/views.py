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
            return redirect('interview_gen:question_gen')  # 저장 후 리디렉션 (예: 로딩페이지or)
    else:
        form = InterviewGenForm()  # GET 요청일 때 빈 폼 표시
    
    context = {
        'form': form,
    }
    return render(request, 'form.html', context) # 다시 폼 보여주기


#def news (회사이름 + 뉴스 api를 통해 최신 뉴스를 검색하는 함수)
#def concat (위에 실행된 내용 + 자소서 결합하는 함수)
#def generate (위에 실행된 내용 기반으로 gpt한테 질문 만들어달라는 함수)


def question_gen(request):
    # 생성된 질문을 가져와서 템플릿에 전달
    latest_interview = InterviewGen.objects.latest('id')
    context = {
        'generated_question': latest_interview.generated_question,
    }
    return render(request, 'question_gen.html', context)
