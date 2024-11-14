from django.urls import path
from . import views
from .views import CustomLoginView


app_name = 'user_mypage'

urlpatterns = [
    path('signup/', views.signup, name='signup'),  # 회원가입 페이지 경로
    path('login/', CustomLoginView.as_view(), name='login'),     # 로그인 페이지 경로
    path('logout/', views.logout, name='logout'),  # 로그아웃 기능 경로
    path('mypage/', views.history, name='mypage'), #히스토리 열람 기능
    path('detail/<int:pk>/', views.detail, name='detail'),  # 질문 상세 보기
]