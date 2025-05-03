# main_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'), 
    path('signup/', views.signup_view, name='signup'), 
    path('save_final_prompt/', views.save_final_prompt, name='save_final_prompt'),
    path('conversation/<int:conversation_id>/', views.view_conversation, name='view_conversation'),
]
from . import views
