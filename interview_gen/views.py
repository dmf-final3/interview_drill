#views.py
from .models import InterviewGen
from .forms import InterviewGenForm
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

#load API key and other necessary imports
import os
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

# 환경 변수에서 네이버 API 인증 정보 불러오기
CLIENT_ID = os.getenv('NAVER_CLIENT_ID')
CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET')
NEWS_SEARCH_URL = "https://openapi.naver.com/v1/search/news.json"


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
            # 폼 데이터를 저장하고 `company_name`을 기준으로 뉴스 데이터를 저장
            interview_init = form.save()
            get_news(interview_init)

            # 이후 다른 API와의 통합을 위해 OpenAI generate 함수를 호출합니다
            generate(openai_api_key, interview_init.id)

            return redirect('interview_gen:question_gen', pk=interview_init.pk)  # 저장 후 리디렉션 (예: 로딩페이지or)
    else:
        form = InterviewGenForm()  # GET 요청일 때 빈 폼 표시
    
    context = {
        'form': form,
    }
    return render(request, 'form.html', context) # 다시 폼 보여주기


def naver_news_crawler(company_name):
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET
    }
    news_list = []
    start = 1

    while len(news_list) < 5:
        params = {
            "query": company_name,  # 검색어 설정
            "display": 10,          # 출력 결과 개수 설정 (최대 10개)
            "start": start,
            "sort": "sim",           # 정렬 방식: 관련도
            "sm" : "tab_opt",
            "pd" : 5,
            "mynews" : 1,
            "office_type" : 3,
        }

        response = requests.get(NEWS_SEARCH_URL, headers=headers, params=params)
        
        if response.status_code != 200:
            print("Error: 네이버 뉴스 API 호출 실패, 상태 코드:", response.status_code)
            return None  # 에러 발생 시 None 반환

        #API 응답에서 기사 목록 추출
        news_items = response.json().get('items', [])
        
        if not news_items: #더 이상 기사가 없을 경우 반복 종료
            break
            
        for item in news_items:
            if len(news_list) >= 5:
                break

            # 각 뉴스 링크를 통해 기사 제목과 본문을 크롤링
            url = item["link"]
            try:
                article_response = requests.get(url)
                article_soup = BeautifulSoup(article_response.text, "html.parser")
                
                # 제목 추출
                title_tag = article_soup.select_one("h2#title_area")
                title = title_tag.get_text() if title_tag and hasattr(title_tag, 'get_text') else None  # get_text() 호출 전 확인
                
                # 본문 추출 (이미지 태그는 제거)
                article_tag = article_soup.select_one("article#dic_area")
                if article_tag:
                    for span in article_tag.select("span.end_photo_org"):
                        span.decompose()  # 이미지 태그 제거
                    article = article_tag.get_text(strip=True)
                else:
                    article = None
                
                # 제목과 본문이 있고 본문 길이가 100자 이상일 경우만 최종 뉴스 데이터 추가
                if title and article and len(article) >= 100:
                    news_item = f"{title}\n{url}\n{article}"
                    news_list.append(news_item)
            
            except Exception as e:
                    print("Error fetching article content from URL:", url, "Error:", e)
        
        start += 10  # 다음 API 호출 시 새로운 기사 목록을 가져오기 위해 시작 인덱스 증가

    # 수집된 5개의 유효한 뉴스 기사를 반환
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

                                    ```html``` 코드를 생략한 후 위와 같은 형식으로 출력해줘. 뉴스 관련 질문 뒤에만 링크를 포함해야 하며, 나머지 질문에는 링크를 달지 말아야 해.
                                    
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