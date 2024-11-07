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
    params = {
        "query": company_name,  # 검색어 설정
        "display": 5,          # 출력 결과 개수 설정 (최대 10개)
        "start": 1,
        "sort": "sim"           # 정렬 방식: 유사도 순
    }
    response = requests.get(NEWS_SEARCH_URL, headers=headers, params=params)
    
    if response.status_code == 200:
        news_items = response.json().get('items', [])
        news_list = []
        
        for item in news_items:
            # 각 뉴스 링크를 통해 기사 제목과 본문을 크롤링
            url = item["link"]
            try:
                article_response = requests.get(url)
                article_soup = BeautifulSoup(article_response.text, "html.parser")
                
                # 제목 추출
                title = article_soup.select_one("h2#title_area").get_text() if article_soup.select_one("h2#title_area") else "제목 없음"
                
                # 본문 추출 (이미지 태그는 제거)
                article_tag = article_soup.select_one("article#dic_area")
                if article_tag:
                    for span in article_tag.select("span.end_photo_org"):
                        span.decompose()  # 이미지 태그 제거
                    article = article_tag.get_text(strip=True)
                else:
                    article = "본문 없음"
                
                # 최종 뉴스 데이터 추가
                news_item = f"{title}\n{url}\n{article}"
                news_list.append(news_item)
            
            except Exception as e:
                print("Error fetching article content from URL:", url, "Error:", e)
        
        # news_content 생성 (리스트를 줄바꿈으로 연결)
        news_content = "\n\n".join(news_list)
        
        return news_content

    else:
        print("Error: 네이버 뉴스 API 호출 실패, 상태 코드:", response.status_code)
        return "뉴스 데이터를 불러올 수 없습니다."


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
                                    너는 이제부터 한글로 면접관과 지원자의 롤플레이를 할거야.

                                    뉴스 본문 정보를 기반으로 한 최신 동향 질문 2개,
                                    면접자의 경험 정보의 구체적인 예시나 일화에 대해 답변을 유도하는 질문 3개,
                                    총 5개의 질문을 작성해줘.

                                    뉴스 본문 정보를 참고할때는 회사에 대한 긍정적인 기사를 중심으로 질문을 생성하고,
                                    추가로 뉴스를 참고하여 생성한 질문 답변의 경우 무조건 참고한 뉴스 링크를 <a href="">관련 뉴스 링크 바로가기</a>를 이용해서 참고한 질문 내용n의 p 태그 마지막에 첨부해줘.
                                    뉴스 본문 정보가 없다면 뉴스 관련 질문을 생략하고 링크를 달아줄 필요도 없어.

                                    면접관은 면접자의 비판적 사고 능력을 판단하는 동시에,
                                    예/아니오나 단답형으로 답변이 나오는 질문은 피하고,
                                    지원자는 입력한 experience의 구체적 예시나 일화를 두괄식으로 잘 드러내는 답변을 작성해야돼.

                                    최종 형태는 html로 표시했을때 아래 예시와 같이 출력해줘.
                                    <p class="question"> 질문 내용1 </p> <p class="answer"> 답변 내용1</p> <p class="question"> 질문 내용2 </p> <p class="answer"> 답변 내용2 </p>
                                    마지막으로 양끝에 html 코드 블럭은 제거해줘.
                                    
                                """
                },
                {'role': 'user',
                'content': f"""
                                                면접자의 경험 정보 : {interview_init.experience},
                                                뉴스 본문 정보: {news_content}
                                            """
                }    
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