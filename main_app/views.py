import json
import os
import pandas as pd
import random

from django.shortcuts import get_object_or_404, render, redirect
from .forms import SignUpForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_protect
from .models import Conversation
from django.http import JsonResponse
from .forms import SignUpForm
from django.views.decorators.csrf import csrf_exempt
from .models import ChatSession, SavedPrompt
from django.contrib.auth.decorators import login_required
from .forms import EditProfileForm
from django.conf import settings

file_path = os.path.join(settings.BASE_DIR, 'style_category.xlsx')
style_df = pd.read_excel(file_path)
style_list = style_df['Category'].dropna().unique().tolist()


# 로그아웃 처리
def logout_view(request):
    logout(request)  
    return redirect('home') 

def home(request):
    chat_id = request.GET.get('chat_id')

    if request.method == 'POST':
        user_prompt = request.POST.get('prompt')
        model_response = "모델이 생성한 응답입니다."

        if request.user.is_authenticated:
            if not chat_id:
                chat_count = ChatSession.objects.filter(user=request.user).count()
                new_chat_id = f"chat_{chat_count + 1}"

                new_session = ChatSession.objects.create(
                    user=request.user,
                    chat_id=new_chat_id,
                    initial_prompt=user_prompt,
                    history=[
                        {"role": "user", "content": user_prompt},
                        {"role": "model", "content": model_response}
                    ]
                )
                return redirect(f"/?chat_id={new_chat_id}")
            else:
                session = get_object_or_404(ChatSession, user=request.user, chat_id=chat_id)
                if not session.initial_prompt:
                    session.initial_prompt = user_prompt
                session.history.append({"role": "user", "content": user_prompt})
                session.history.append({"role": "model", "content": model_response})
                session.save()
                return redirect(f"/?chat_id={chat_id}")
        else:
            if 'chat_sessions' not in request.session:
                request.session['chat_sessions'] = []
            if not chat_id:
                chat_id = f"chat_{len(request.session['chat_sessions']) + 1}"
                new_session = {
                    "chat_id": chat_id,
                    "initial_prompt": user_prompt,
                    "history": [
                        {"role": "user", "content": user_prompt},
                        {"role": "model", "content": model_response}
                    ]
                }
                request.session['chat_sessions'].append(new_session)
                request.session.modified = True
                return redirect(f"/?chat_id={chat_id}")
            else:
                for session in request.session['chat_sessions']:
                    if session['chat_id'] == chat_id:
                        if not session.get('initial_prompt'):
                            session['initial_prompt'] = user_prompt
                        session['history'].append({"role": "user", "content": user_prompt})
                        session['history'].append({"role": "model", "content": model_response})
                        request.session.modified = True
                        break
                return redirect(f"/?chat_id={chat_id}")

    if request.user.is_authenticated:
        chat_sessions = ChatSession.objects.filter(user=request.user).order_by('created_at')
        full_name = request.user.get_full_name()
        if not full_name:  # full_name이 비어있으면 username 사용
            full_name = request.user.username
    else:
        chat_sessions = request.session.get('chat_sessions', [])
        full_name = None

    selected_chat = None
    if chat_id:
        if request.user.is_authenticated:
            selected_chat = get_object_or_404(ChatSession, user=request.user, chat_id=chat_id)
        else:
            for session in chat_sessions:
                if session['chat_id'] == chat_id:
                    selected_chat = session
                    break

    # 랜덤 추천 스타일 3개 뽑기
    recommended_styles = random.sample(style_list, 3)

    return render(request, 'home.html', {
        'chat_sessions': chat_sessions,
        'selected_chat': selected_chat,
        'recommended_styles': recommended_styles,
        'full_name': full_name, 
    })


# 회원가입
def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '회원가입이 완료되었습니다!')
            return redirect('login')  
        else:
            messages.error(request, '입력 정보를 다시 확인해 주세요.')
            print(form.errors) 
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

# 로그인
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')  
        else:
            messages.error(request, '아이디 또는 비밀번호가 올바르지 않습니다.')
    return render(request, 'login.html')
    

# 내 정보 보기
def profile_view(request):
    return render(request, 'profile.html')

@csrf_protect
def my_view(request):
    return render(request, 'my_template.html')


def view_conversation(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)
    return render(request, 'conversation_detail.html', {'conversation': conversation})

def your_view(request):
    if request.method == 'POST':
        user_prompt = request.POST.get('prompt')

        if 'history' not in request.session:
            request.session['history'] = []

        if len(request.session['history']) == 0:
            request.session['history'].append({'prompt': user_prompt})

        request.session.modified = True

        response = your_model_answer(user_prompt)

        # ⭐ first_name이 비어 있으면 username 사용
        user_name = request.user.first_name or request.user.username

        return render(request, 'your_template.html', {
            'prompt': user_prompt,
            'response': response,
            'history': request.session['history'],
            'user_name': user_name,
        })

def reset_conversations(request):
    if request.user.is_superuser:
        ChatSession.objects.all().delete()
        return redirect('home')
    else:
        return redirect('home')


@csrf_exempt # CSRF 관련 부분은 필요에 따라 유지 또는 수정
def save_final_prompt(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({'message': '비로그인 사용자는 저장할 수 없습니다.'}, status=403)

        try:
            data = json.loads(request.body)
            chat_id = data.get('chat_id')
            selected_prompt = data.get('model_response')
            model_outputs = data.get('model_outputs', [])
            reason = data.get('reason', '')

            session = get_object_or_404(ChatSession, user=request.user, chat_id=chat_id)
            initial_prompt = session.initial_prompt
            if not initial_prompt: # 초기 프롬프트가 있어야 의미있을 듯
                 return JsonResponse({'message': '저장할 초기 프롬프트가 없습니다.'}, status=400)
            if not selected_prompt:
                 return JsonResponse({'message': '선택된 프롬프트가 없습니다.'}, status=400)


            # --- CSV 저장 로직 대신 아래 DB 저장 로직 사용 ---
            SavedPrompt.objects.create(
                user=request.user,
                chat_session=session,
                initial_prompt=initial_prompt,
                selected_prompt=selected_prompt,
                model_outputs=model_outputs,
                reason=reason
            )
            # --- 여기까지 ---

            return JsonResponse({'message': '데이터베이스에 프롬프트가 저장되었습니다.'})

        except ChatSession.DoesNotExist:
             return JsonResponse({'message': '채팅 세션을 찾을 수 없습니다.'}, status=404)
        except Exception as e:
            # 실제 서비스에서는 에러 로깅 등 필요
            print(f"Error saving prompt: {e}") # 개발 중 에러 확인용
            return JsonResponse({'message': '프롬프트 저장 중 오류가 발생했습니다.'}, status=500)

    return JsonResponse({'message': '잘못된 요청입니다.'}, status=400)



@csrf_exempt
def new_chat(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            chat_count = ChatSession.objects.filter(user=request.user).count()
            new_chat_id = f"chat_{chat_count + 1}"

            ChatSession.objects.create(
                user=request.user,
                chat_id=new_chat_id,
                initial_prompt="",
                history=[]
            )

            return JsonResponse({'chat_id': new_chat_id})

        else:
            if 'chat_sessions' not in request.session:
                request.session['chat_sessions'] = []

            new_chat_id = f"chat_{len(request.session['chat_sessions']) + 1}"
            new_session = {
                "chat_id": new_chat_id,
                "initial_prompt": "",
                "history": []
            }
            request.session['chat_sessions'].append(new_session)
            request.session.modified = True

            return JsonResponse({'chat_id': new_chat_id})

    return JsonResponse({'message': '잘못된 요청입니다.'}, status=400)

def your_view(request):
    user_name = request.user.first_name  # 또는 username, 또는 profile.name
    recommended_styles = ["minimalist", "cosmic", "cyberpunk"]
    return render(request, 'your_template.html', {
        'user_name': user_name,
        'recommended_styles': recommended_styles,
    })

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '내 정보가 수정되었습니다.')
            return redirect('profile') 
    else:
        form = EditProfileForm(instance=request.user)
    
    return render(request, 'edit_profile.html', {'form': form})


