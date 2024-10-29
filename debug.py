import os
from dotenv import load_dotenv
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
import openai

# 환경 변수 로드
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

# Django 설정 모듈 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_drill.settings')
import django
django.setup()

from django.shortcuts import get_object_or_404

class OpenAI:
    def __init__(self, api_key):
        self.api_key = api_key

    class ChatCompletion:
        def create(self, model, messages):
            return {
                'choices': [
                    {'message': {'content': 'Generated question 1\nGenerated question 2\nGenerated question 3\nGenerated question 4\nGenerated question 5'}}
                ]
            }

    chat = ChatCompletion()

class InterviewGen:
    def __init__(self, experience):
        self.experience = experience
        self.generated_question = ""

    def save(self):
        print("Interview questions saved:", self.generated_question)

def generate(api_key, pk):
    # 임시로 인터뷰 데이터 객체 생성
    interview_init = InterviewGen("Example experience")
    try:
        client = OpenAI(api_key=api_key)
        completion = client.chat.create(
            model='gpt-4o-mini',
            messages=[
                {'role': 'system', 'content': '너는 실무자이자 면접관이야...'},
                {'role': 'user', 'content': interview_init.experience},
            ]
        )

        questions = completion['choices'][0]['message']['content']
        print("Generated Questions:", questions)
        interview_init.generated_question = questions
        interview_init.save() # 데이터베이스에 업데이트

        return questions
    except Exception as e:
        print("Error during OpenAI API call:", str(e))
        return "Error generating questions: " + str(e)

# 실제로 생성한 API 키와 인터뷰 데이터의 PK를 입력
print(generate('your_openai_api_key', 1))







# df = pd.read_csv('df_24.csv')

# results = []


# for index, row in df.iterrows():
#     headline = row['headline']
#     press = row['press']
#     result = openai(OPENAI_API_KEY, headline)
#     results.append({
#         'Press': press,
#         'Headline': headline,
#         'Analysis': result
#     })



# # 결과를 데이터프레임으로 변환
# results_df = pd.DataFrame(results)

# # 결과를 CSV 파일로 저장
# results_df.to_csv('2024_log.csv', index=False)



# def generate_interview_questions(api_key, concat, experience):
#         # AI API 호출 (예시: OpenAI)
#         prompt = f"""
#         사용자 정보:
#         - 회사: {interview_gen.company_name}
#         - 경험: {interview_gen.experience}
#         - 자소서 + 뉴스데이터: {interview_gen.concat}
        
        
#         면접 질문과 예상 답변을 생성하세요.
#         """
#         response = openai.Completion.create(
#             model="gpt-3.5-turbo",
#             prompt=prompt,
#             max_tokens=500,
#             n=3,
#             stop=None,
#             temperature=0.7
#         )
#         return [{"question": q['text'], "answer": "자동 생성된 답변"} for q in response['choices']]