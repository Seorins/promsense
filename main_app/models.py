from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group, Permission

class CustomUser(AbstractUser):
    full_name = models.CharField(max_length=100)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('M', '남자'), ('F', '여자')])
    address = models.CharField(max_length=255)
    address_detail = models.CharField(max_length=255)

    # groups와 user_permissions의 related_name을 지정하여 충돌을 피함
    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',  # 그룹의 역참조 이름을 지정
        blank=True
    )
    
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_set',  # 사용자 권한의 역참조 이름을 지정
        blank=True
    )

    def __str__(self):
        return self.username
    
class Conversation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # 커스텀 User 모델을 사용
    prompt = models.TextField()  # 사용자 입력
    response = models.TextField()  # 모델 응답
    status = models.CharField(max_length=20, default='in_progress')  # 대화 상태 (진행 중 / 종료)
    is_liked = models.BooleanField(default=False)  # 사용자가 좋아요를 눌렀는지 여부
    created_at = models.DateTimeField(auto_now_add=True)  # 대화 생성 시각

    def __str__(self):
        return f"대화 #{self.id} - {self.user.username}"

    class Meta:
        ordering = ['-created_at']

class ChatSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    chat_id = models.CharField(max_length=100)
    initial_prompt = models.TextField()
    history = models.JSONField(default=list)  # user, model 주고받은 대화 기록
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.chat_id}"