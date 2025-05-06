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

    # # groups와 user_permissions의 related_name을 지정하여 충돌을 피함
    # groups = models.ManyToManyField(
    #     Group,
    #     related_name='customuser_set',  # 그룹의 역참조 이름을 지정
    #     blank=True
    # )
    
    # user_permissions = models.ManyToManyField(
    #     Permission,
    #     related_name='customuser_set',  # 사용자 권한의 역참조 이름을 지정
    #     blank=True
    # )

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
    
    # main_app/models.py 파일 맨 아래 등에 추가

class SavedPrompt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="사용자")
    chat_session = models.ForeignKey(ChatSession, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="채팅 세션") # 어떤 채팅에서 저장했는지 연결 (선택사항)
    initial_prompt = models.TextField(blank=True, verbose_name="초기 프롬프트")
    selected_prompt = models.TextField(verbose_name="선택된 프롬프트(응답)")
    model_outputs = models.JSONField(default=list, verbose_name="전체 모델 응답") # 전체 응답 목록 저장
    reason = models.CharField(max_length=100, blank=True, verbose_name="선택 이유") # 선택 이유
    saved_at = models.DateTimeField(auto_now_add=True, verbose_name="저장 시각")

    def __str__(self):
        return f"{self.user.username} - Saved Prompt {self.id}"

    class Meta:
        verbose_name = "저장된 프롬프트"
        verbose_name_plural = "저장된 프롬프트 목록"
        ordering = ['-saved_at']



# models.py 파일 맨 아래 등에 추가 (기존 코드 아래에)

class DemoQA(models.Model):
    """
    데모 시연을 위한 미리 정의된 질문과 답변을 저장하는 모델
    """
    question = models.TextField(unique=True, verbose_name="데모 질문")  # 데모용 질문 (고유해야 함)
    answer = models.TextField(verbose_name="데모 답변")              # 데모용 답변
    category = models.CharField(max_length=100, blank=True, null=True, verbose_name="카테고리 (선택)") # 질문 분류 (선택 사항)
    # created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일") # 필요하다면 생성일 추가

    def __str__(self):
        return f"데모 질문: {self.question[:50]}" # 어드민 등에서 보일 때 질문 앞부분만 표시

    class Meta:
        verbose_name = "데모 질문/답변"
        verbose_name_plural = "데모 질문/답변 목록"
        ordering = ['id'] # 또는 'category', 'question' 등 원하는 순서로 정렬