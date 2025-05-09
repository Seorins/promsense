from django.contrib import admin
from django.urls import path, include
from main_app import views
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main_app.urls')),
    path('accounts/', include('allauth.urls')),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('signup/', views.signup_view, name='signup'),
    path('reset_conversations/', views.reset_conversations, name='reset_conversations'),
    path('new_chat/', views.new_chat, name='new_chat'),
    path('save_final_prompt/', views.save_final_prompt, name='save_final_prompt'),  
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('api/demo_qa/', views.demo_qa_api, name='demo_qa_api'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)