from django.contrib import admin
from django.urls import path, include
from main_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main_app.urls')),
    path('accounts/', include('allauth.urls')),
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('signup/', views.signup_view, name='signup'),
    path('reset_conversations/', views.reset_conversations, name='reset_conversations'),
    path('new_chat/', views.new_chat, name='new_chat'),
    path('save_final_prompt/', views.save_final_prompt, name='save_final_prompt'),  
    path('edit_profile/', views.edit_profile, name='edit_profile'),
]