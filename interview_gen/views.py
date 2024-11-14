#views.py
from .models import InterviewGen
from .forms import InterviewGenForm
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

#load API key and other necessary imports
import os
import time
import json
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
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
        form = InterviewGenForm(request.POST)  # 파일 처리가 필요한 경우에만 request.FILES 포함
        if form.is_valid():
            interview_gen = form.save(commit=False)
            if request.user.is_authenticated:
                interview_gen.user = request.user
            interview_gen.save()

            # 뉴스 데이터 생성 및 저장
            get_news(interview_gen)

            # OpenAI를 사용하여 질문 생성
            try:
                # 환경 변수에서 OpenAI API 키 로드
                api_key = os.getenv('OPENAI_API_KEY')
                generate(api_key, interview_gen.id)
            except Exception as e:
                return HttpResponse("Error generating questions: " + str(e))

            # 생성된 질문 페이지로 리다이렉트
            return redirect('interview_gen:question_gen', pk=interview_gen.pk)
    else:
        form = InterviewGenForm()

    return render(request, 'interview_gen/create.html', {'form': form})


def naver_news_crawler(company_name):
    base_url = "https://search.naver.com/search.naver"
    
    news_list = []
    start = 1  # 검색 시작 지점 (10개씩 넘기면서 다음 페이지로 이동)

    while len(news_list) < 5:  # 뉴스 기사 5개 수집할 때까지 반복
        params = {
            "where": "news",
            "query": company_name,
            "sm": "tab_opt",        # 네이버 검색 최적화 옵션
            "sort": "0",            # 최신순 정렬 (0: 관련도, 1: 최신순, 2: 오래된 순)
            "office_category": 3,  # 전문지 설정
            "pd": "5",              # 특정 기간 설정
            "nso": "so:r,p:1y",     # 1년 범위 내 최신순 정렬
            "start": start,         # 시작 인덱스 (10씩 증가하여 다음 페이지로 이동)
            "display": 10,  # 한 페이지에 보여줄 기사 수
            "start": start,
        }
        # 요청 전 최종 URL 확인용 디버그 코드
        print(f"Requesting page with start={start}, params={params}")
        
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()  # HTTP 에러 발생 시 예외 처리
            # 최종 URL 확인
            print("Final URL:", response.url)  # 최종 URL이 파라미터와 함께 생성되었는지 확인
            # HTML 파싱
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.select('ul.list_news > li')

            if not articles:  # 더 이상 기사가 없을 경우 반복 종료
                print("No more articles found.")
                break

            for article in articles:
                if len(news_list) >= 5:
                    break
                
                title_tag = article.select_one('a.news_tit')
                summary_tag = article.select_one('div.news_dsc')
                
                # 제목과 요약 본문이 있을 때만 추가
                if title_tag and summary_tag:
                    title = title_tag.get_text(strip=True)
                    link = title_tag['href']
                    summary = summary_tag.get_text(strip=True)
                    news_item = f"{title}\n{link}\n{summary}"
                    news_list.append(news_item)
                    
        except requests.exceptions.RequestException as e:
            print("Request failed:", e)
            break

        # 다음 페이지로 이동하기 위해 시작 인덱스 증가
        start += 10
    
    # 최종 수집된 뉴스 기사 리스트를 반환
    return "\n\n".join(news_list) if news_list else None


# 크롤링한 뉴스 데이터를 데이터베이스에 저장하는 함수
def get_news(interview_init):
    # company_name을 기준으로 뉴스 본문을 직접 생성하여 저장
    news_content = naver_news_crawler(interview_init.company_name)
    interview_init.news_group = news_content
    interview_init.save()


def generate(api_key, pk):
    # 저장된 인터뷰 데이터 객체를 조회
    interview_init = get_object_or_404(InterviewGen, pk=pk)

    # news_group을 파싱 없이 바로 사용
    news_content = interview_init.news_group or "뉴스 내용이 없습니다."

    try:
        client = OpenAI(api_key=api_key)
        completion = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {
                    'role': 'system', 
                    'content': """
                                    너는 이제부터 한글로 면접관과 지원자의 롤플레이를 할 거야.

                                    아래 조건에 맞춰 총 5개의 질문을 작성해줘.
                                    
                                    - **첫 번째 섹션**: 면접관은 최신 동향 관련 질문 2개를 먼저 작성해줘.
                                    * 이 질문들은 뉴스 본문 정보를 참고하여 작성하고, 뉴스 관련된 답변에만 뉴스 링크를 추가해야 해.
                                    * 참조하는 뉴스 링크는 서로 중복되지 않아야 하고 면접 질문, 답변 그리고 뉴스의 내용은 서로 연관이 있어야 돼.
                                    * 지원자는 해당 답변 시 경험 정보를 복합적으로 활용한 답변을 제시해도 좋아.
                                    * 지원자의 답변 바로 뒤에 뉴스 링크를 넣어야 하며, 형식은 <a href="링크" target="_blank">관련 뉴스 링크 바로가기</a>와 같아야 해.
                                    
                                    - **두 번째 섹션**: 지원자의 경험 정보와 관련된 질문 3개를 작성해줘.
                                    * 면접관은 이 질문을 통해 지원자의 경험 정보에서 구체적인 예시나 일화를 유도해야해.
                                    * 지원자는 experience의 구체적 예시나 일화를 두괄식으로 잘 드러내는 답변을 작성하되 experience에 정보가 부족할 경우 키워드를 조합해서 알맞는 경험을 적당히 창작해도 좋아.
                                    * 이 섹션의 질문에는 뉴스 링크를 추가하지 말아줘.

                                    최종 출력은 HTML 형태로, 아래 예시처럼 작성해줘:
                                    <p class="question">질문 내용 1</p><p class="answer">답변 내용 1 <br></br><a href="링크" target="_blank">관련 뉴스 링크 바로가기</a></p>
                                    <p class="question">질문 내용 2</p><p class="answer">답변 내용 2 <br></br><a href="링크" target="_blank">관련 뉴스 링크 바로가기</a></p>
                                    <p class="question">질문 내용 3</p><p class="answer">답변 내용 3</p>
                                    <p class="question">질문 내용 4</p><p class="answer">답변 내용 4</p>
                                    <p class="question">질문 내용 5</p><p class="answer">답변 내용 5</p>
                                    ```html```코드를 생략한 후 위와 같은 형식으로 출력해줘. 뉴스 관련 질문 뒤에만 링크를 포함해야 하며, 나머지 질문에는 링크를 달지 말아야 해.
                                    
                                """
                },
                {'role': 'user',
                'content': f"""
                                                지원자의 경험 정보 : {interview_init.experience},
                                                뉴스 본문 정보: {news_content}
                                            """
                }    
            ],
            temperature=0.5
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