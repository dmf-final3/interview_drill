from django.urls import path
from . import views

app_name = 'interview_gen'

urlpatterns = [
    path('', views.index, name='index'),
    path('create/', views.create, name='create'),
    path('generate/<int:pk>/', views.generate, name='generate'),
    path('question_gen/<int:pk>/', views.question_gen, name='question_gen'),
    #path('question_gen/', views.question_gen, name='question_gen'),

]