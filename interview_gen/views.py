#views.py
from .models import InterviewGen
from .forms import InterviewGenForm
from django.shortcuts import render, redirect, get_object_or_404

#load API key and other necessary imports
import os
from dotenv import load_dotenv
# .env 파일을 로드합니다.
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)
# 로드한 환경 변수에서 OPENAI_API_KEY 가져오기
openai_api_key = os.getenv('OPENAI_API_KEY')
from django.conf import settings
from openai import OpenAI



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
            interview_init = form.save()

            generate(openai_api_key, interview_init.id)

            return redirect('interview_gen:question_gen', pk=interview_init.pk)  # 저장 후 리디렉션 (예: 로딩페이지or)
    else:
        form = InterviewGenForm()  # GET 요청일 때 빈 폼 표시
    
    context = {
        'form': form,
    }
    return render(request, 'form.html', context) # 다시 폼 보여주기


#def news (회사이름 + 뉴스 api를 통해 최신 뉴스를 검색하는 함수)
#def concat (위에 실행된 내용 + 자소서 결합하는 함수)


#def generate (위에 실행된 내용 기반으로 gpt한테 질문 만들어달라는 함수)
def generate(api_key, pk):
    # 저장된 인터뷰 데이터 객체를 조회
    interview_init = get_object_or_404(InterviewGen, pk=pk)

    try:
        client = OpenAI(api_key=api_key)
        completion = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {
                    'role': 'system', 
                    'content': """
                                    너는 실무자이자 면접관이야. 
                                    면접자의 비판적 사고 능력 등을 판단하는 동시에, 
                                    experience의 구체적 예시나 일화에 대해 답변을 유도하는 면접 질문을 5개 생성해줘. 
                                    예/ 아니오나 명백한 답변이 있는 질문은 피하고, 
                                    최신 이슈나 뉴스 동향을 알 수 있는 질문도 최대 2개 까지 포함시켜줘.

                                    최종 형태는 html에 넣기 위해 적절한 태그들로 감싸서 출력해줘. 코드블럭으로 감싸는 코드도 제거해줘
                                """
                },
                {'role': 'user', 'content': interview_init.experience},
            ]
        )

        questions = completion.choices[0].message.content


        # 생성된 질문을 인터뷰 객체에 저장하고 데이터베이스에 업데이트
        interview_init.generated_question = questions
        interview_init.save()

    
    except Exception as e:
        # API 호출 중 발생하는 오류를 디버깅하기 위해 예외 메시지 출력
        return HttpResponse("Error generating questions: " + str(e))


def question_gen(request, pk):
    # 생성된 면접 질문을 불러오기 위해 InterviewGen 객체를 조회
    interview_init = get_object_or_404(InterviewGen, pk=pk)

    context = {
        'generated_question': interview_init.generated_question,
    }

    return render(request, 'question_gen.html', context)
