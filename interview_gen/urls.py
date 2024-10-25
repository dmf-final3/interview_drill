from django.urls import path
from . import views

app_name = 'interview_gen'

urlpatterns = [
    path('', views.index, name='index'),
]