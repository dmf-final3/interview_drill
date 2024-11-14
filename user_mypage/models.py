from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class Mypage(AbstractUser):
    major = models.CharField(max_length=100)
    desired_job = models.CharField(max_length=100)