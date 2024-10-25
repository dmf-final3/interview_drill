from django.db import models

# Create your models here.
class InterviewGen(models.Model):
    company_name = models.CharField(max_length=50) #회사이름(지망기업)
    experience = models.TextField() #관련경험(자소서)
    news_group = models.TextField() #뉴스모음
    generated_question = models.TextField() #생성된 질문
