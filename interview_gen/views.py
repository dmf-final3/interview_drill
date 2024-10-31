#views.py
from .models import InterviewGen
from .forms import InterviewGenForm
from django.shortcuts import render, redirect, get_object_or_404

#load API key and other necessary imports
from openai import OpenAI
from django.http import HttpResponse
import os
from dotenv import load_dotenv
# .env 파일을 로드합니다.
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)
# 로드한 환경 변수에서 OPENAI_API_KEY 가져오기
openai_api_key = os.getenv('OPENAI_API_KEY')




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
                                    너는 이제부터 면접관과 면접자의 롤플레이를 할거야.
                                    면접관의 대화는 다음 조건에 맞게 생성해줘.
                                    1.면접자의 비판적 사고 능력 등을 판단하는 동시에, 
                                    2.experience의 구체적 예시나 일화에 대해 답변을 유도하는 면접 질문을 5개 생성해줘. 
                                    3.예/ 아니오나 명백한 답변이 있는 질문은 피하고, 
                                    4.뉴스 본문 정보에 대한 의견을 묻는 질문도 최대 2개까지 포함시켜줘.
                                    5.반향어는 최대한 삼가고 실제 지원자에게 말을 거는 듯한 말투로 질문을 작성해줘.
                                    면접자의 대화는 다음 조건에 맞게 생성해줘.
                                    1.입력한 experience의 구체적 예시나 일화를 두괄식으로 잘 드러내는 답변을 작성해줘.
                                    2.뉴스와 관련된 질문은 뉴스 본문 정보에서 답을 찾고 experience의 강점과 연결시켜줘.
                                    3.마지막으로 이 기업에서 어떤 역할을 수행할 수 있을지 잘 드러나는 답변을 작성해줘.
                                    최종 형태는 면접 질문1, 면접 답변1, 면접 질문2, 면접 답변2...와 같은 형태로 h 태그로 감싸서 출력하고 양 끝에 코드블럭은 제거해줘.
                                """
                },
                {'role': 'user', 'content': f"""
                                                면접자의 경험 정보 : {interview_init.experience},
                                                뉴스 본문 정보: [파이낸셜뉴스] 글로벌 바이오센서 전문기업 아이센스가 지난 5월 28일 삼성전자가 주최한 ‘삼성 헬스 파트너 데이’에 참가해 협업 추진 사례를 발표했다고 5일 밝혔다.

이번 행사는 건강 관리 플랫폼 ‘삼성 헬스(Samsung Health)’ 파트너들과 디지털 헬스 케어 비전을 공유하고 삼성 헬스 생태계 확장을 위해 삼성전자가 개최한 최초 파트너 데이다.

이번 행사에서 아이센스 이광현 상무가 “삼성 헬스와 함께하는 혁신적인 혈당 모니터링”이라는 주제로 아이센스의 연속혈당측정기 제품인 케어센스 에어(CareSens Air)와 삼성 헬스 서비스와의 협업 추진 사례를 발표했다.

아이센스 이광현 상무는 “삼성 헬스와의 협력을 통해 케어센스 에어 앱에서 삼성 헬스로 연속 혈당 데이터의 공유가 가능하며 삼성 헬스 앱에서 혈당에 영향을 주는 활동, 운동, 수면, 식사 등과 같은 데이터를 연속혈당 데이터와 같이 볼 수 있어 사용자의 건강한 생활 습관 형성을 위한 인사이트를 제공할 수 있는 의미 있는 협업 사례”라고 설명했다. 또한, “향후 삼성전자의 갤럭시 워치와의 추가적인 협업을 통해 사용자들에게 언제 어디서나 자신의 혈당을 모니터링 하면서 건강을 관리할 수 있도록 하자”라고 제안했다.

아이센스는 삼성 헬스 파트너로 참여하면서 삼성 헬스 소프트웨어 개발 키트(SDK)를 기반으로 건강관리 서비스를 추진하는 많은 파트너들사에게 연속혈당측정 데이터를 제공할 예정이다. 이를 통해 삼성 헬스 생태계 확장과 케어센스 에어 간 시너지를 극대화할 방침이다.

아이센스 남학현 대표이사도 “이번 행사에서 케어센서 에어 제품이 삼성 헬스 앱과 시너지를 낼 수 있는 점을 소개할 수 있어 기쁘다”라며 “앞으로도 지속적인 기술 혁신과 글로벌 시장 확대를 추진하고 삼성 헬스와의 협업을 통해 연속혈당측정 데이터가 소비자로부터 조금 더 의미 있게 활용될 수 있도록 노력할 계획”이라고 부연했다.
                                            """
                },    
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
