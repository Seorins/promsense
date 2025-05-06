from django.contrib import admin
from .models import CustomUser, Conversation, ChatSession, SavedPrompt, DemoQA # DemoQA 추가

admin.site.register(CustomUser)

@admin.register(DemoQA)
class DemoQAAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'answer', 'category')
    search_fields = ('question', 'answer', 'category')
    list_filter = ('category',)