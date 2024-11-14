from django.db import models
from user_mypage.models import Mypage

# Create your models here.
class InterviewGen(models.Model):
    company_name = models.CharField(max_length=50) #회사이름(지망기업)
    experience = models.TextField() #관련경험(자소서)
    news_group = models.TextField(blank=True) #뉴스모음
    generated_question = models.TextField(blank=True) #생성된 질문
    user = models.ForeignKey(Mypage, on_delete=models.CASCADE, related_name='interviews', null=True)