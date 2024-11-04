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
                news_item = {
                    "title": title,
                    "link": url,
                    "article": article
                }
                news_list.append(news_item)
            
            except Exception as e:
                print("Error fetching article content from URL:", url, "Error:", e)
        
        # 디버깅: 크롤링된 뉴스 리스트 확인
        #print("DEBUG: 크롤링된 뉴스 리스트:", news_list)
        return news_list
    
    else:
        print("Error: 네이버 뉴스 API 호출 실패, 상태 코드:", response.status_code)
        return []

# 크롤링한 뉴스 데이터를 데이터베이스에 저장하는 함수
def get_news(interview_init):
    # 회사 이름을 통해 뉴스 크롤링
    news_data = naver_news_crawler(interview_init.company_name)
    
    # JSON 형식의 문자열로 변환하여 news_group 컬럼에 저장
    interview_init.news_group = news_data
    interview_init.save()


#def generate (위에 실행된 내용 기반으로 gpt한테 질문 만들어달라는 함수)
def generate(api_key, pk):
    # 저장된 인터뷰 데이터 객체를 조회
    interview_init = get_object_or_404(InterviewGen, pk=pk)

    # `news_group`이 JSON 형식인지 확인 후 파싱
    try:
        news_group = json.loads(interview_init.news_group) if interview_init.news_group else []
    except json.JSONDecodeError:
        news_group = []  # JSON 형식이 아니면 빈 리스트로 설정하여 오류 방지


    # 뉴스 본문 정보를 생성
    news_content = "\n".join([f"{item['title']}: {item['link']}\n{item['article']}" for item in news_group])
    print(news_content)

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
                                    6.뉴스 본문 정보를 참고할때는 주식 관련이나 부정적 내용은 최대한 배제하고 회사에 대한 긍정적인 기사를 중심으로 질문을 생성해줘.
                                    면접자의 대화는 다음 조건에 맞게 생성해줘.
                                    1.입력한 experience의 구체적 예시나 일화를 두괄식으로 잘 드러내는 답변을 작성해줘.
                                    2.뉴스와 관련된 질문은 뉴스 본문 정보에서 답을 찾아서 제시해줘.
                                    3.마지막으로 이 기업에서 어떤 역할을 수행할 수 있을지 잘 드러나는 답변을 작성해줘.
                                    최종 형태는 html로 표시했을때 다음과 같이 출력하고
                                    <h2>면접 질문1</h2> <p>질문 내용1</p> <h2>면접 답변1</h2> <p>답변 내용1</p> <h2>면접 질문2</h2> <p>질문 내용2</p>
                                    양끝에 html 코드 블럭은 제거해줘.
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