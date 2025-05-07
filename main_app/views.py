import json
import os
import pandas as pd
import random
import requests

from django.shortcuts import get_object_or_404, render, redirect
from .forms import SignUpForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_protect
from .models import Conversation
from django.http import JsonResponse
from .forms import SignUpForm
from django.views.decorators.csrf import csrf_exempt
from .models import ChatSession
from django.contrib.auth.decorators import login_required
from .forms import EditProfileForm
from django.conf import settings
from dotenv import load_dotenv
from .models import DemoQA
import time

excel_file_path = os.path.join(settings.BASE_DIR, 'style_category.xlsx')

try:
    style_df = pd.read_excel(excel_file_path)
    style_list = style_df['Category'].dropna().unique().tolist()

except FileNotFoundError:
    print(f"Excel 파일을 찾을 수 없습니다. 경로: {excel_file_path}")
    style_list = [] 

load_dotenv()

# 로그아웃 처리
def logout_view(request):
    logout(request)  
    return redirect('home') 

def home(request):
    chat_id = request.GET.get('chat_id')
    # GET 요청 부분은 기존과 거의 동일하게 유지됩니다.
    # ... (GET 요청 처리 로직) ...

    if request.method == 'POST':
        user_prompt = request.POST.get('prompt')
        model_response = ""
        new_chat_created_for_ajax = False
        returned_chat_id = chat_id # AJAX 응답에 사용될 chat_id

        # --- DemoQA 또는 API 호출로 model_response 생성 ---
        try:
            demo_entry = DemoQA.objects.get(question__iexact=user_prompt.strip())
            model_response = demo_entry.answer
        except DemoQA.DoesNotExist:
            model_response = "죄송합니다, 이 질문에 대해서는 준비된 데모 답변이 없습니다."
        except Exception as e:
            print(f"DemoQA 조회 중 오류 발생: {e}")
            model_response = "데모 답변을 가져오는 중 오류가 발생했습니다."

        if model_response:
            delay_seconds = random.uniform(2.5, 3.0) # AJAX에서는 조금 짧게 해도 체감이 됩니다.
            print(f"답변 전송 전 {delay_seconds:.2f}초 지연...")
            time.sleep(delay_seconds)

        # --- 채팅 세션 및 히스토리 저장 로직 (기존 로직 활용) ---
        if request.user.is_authenticated:
            if not chat_id: # 새 채팅 생성
                chat_count = ChatSession.objects.filter(user=request.user).count()
                new_chat_id_val = f"chat_{chat_count + 1}"
                ChatSession.objects.create(
                    user=request.user,
                    chat_id=new_chat_id_val,
                    initial_prompt=user_prompt,
                    history=[
                        {"role": "user", "content": user_prompt},
                        {"role": "model", "content": model_response}
                    ]
                )
                returned_chat_id = new_chat_id_val
                new_chat_created_for_ajax = True
            else: # 기존 채팅에 추가
                session_obj = get_object_or_404(ChatSession, user=request.user, chat_id=chat_id)
                if not session_obj.initial_prompt:
                    session_obj.initial_prompt = user_prompt
                session_obj.history.append({"role": "user", "content": user_prompt})
                session_obj.history.append({"role": "model", "content": model_response})
                session_obj.save()
                returned_chat_id = chat_id
        else: # 비로그인 사용자 (세션 기반)
            if 'chat_sessions' not in request.session:
                request.session['chat_sessions'] = []

            if not chat_id: # 새 채팅 생성 (비로그인)
                new_chat_id_val = f"chat_{len(request.session['chat_sessions']) + 1}"
                new_session_data = {
                    "chat_id": new_chat_id_val,
                    "initial_prompt": user_prompt,
                    "history": [
                        {"role": "user", "content": user_prompt},
                        {"role": "model", "content": model_response}
                    ]
                }
                request.session['chat_sessions'].append(new_session_data)
                returned_chat_id = new_chat_id_val
                new_chat_created_for_ajax = True
            else: # 기존 채팅에 추가 (비로그인)
                session_updated = False
                for session_data_item in request.session['chat_sessions']:
                    if session_data_item['chat_id'] == chat_id:
                        if not session_data_item.get('initial_prompt'):
                            session_data_item['initial_prompt'] = user_prompt
                        session_data_item['history'].append({"role": "user", "content": user_prompt})
                        session_data_item['history'].append({"role": "model", "content": model_response})
                        session_updated = True
                        returned_chat_id = chat_id
                        break
                if not session_updated: # 혹시 모를 오류 방지
                     # 이 경우, 새 채팅을 만들어주거나 오류를 반환할 수 있습니다.
                     # 여기서는 단순화를 위해 오류를 가정하지 않겠습니다.
                     pass
            request.session.modified = True


        # --- AJAX 요청인지 확인하고 분기 ---
        # 'X-Requested-With' 헤더는 많은 JavaScript 라이브러리가 AJAX 요청 시 추가합니다.
        # 'Accept' 헤더로 'application/json'을 선호한다고 명시할 수도 있습니다.
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
                  "application/json" in request.META.get('HTTP_ACCEPT', '')

        if is_ajax:
            return JsonResponse({
                'user_prompt': user_prompt,
                'model_response': model_response,
                'chat_id': returned_chat_id, # 현재 또는 새로 생성된 chat_id
                'new_chat_created': new_chat_created_for_ajax, # 새 채팅 여부
                # 필요하다면 전체 히스토리를 보내줄 수도 있지만, 보통은 새 메시지만 보냅니다.
                # 'history': [...]
            })
        else:
            # AJAX가 아닐 경우 기존의 redirect 방식 사용 (JavaScript 비활성화 대비)
            if new_chat_created_for_ajax:
                return redirect(f"/?chat_id={returned_chat_id}")
            else:
                return redirect(f"/?chat_id={chat_id if chat_id else returned_chat_id}")


    # --- GET 요청 처리 ---
    # (기존 GET 요청 로직: chat_sessions, selected_chat, recommended_styles, full_name 등 설정)
    # 이 부분은 AJAX POST 요청과는 별개로, 페이지 초기 로딩 시 사용됩니다.
    if request.user.is_authenticated:
        chat_sessions_qs = ChatSession.objects.filter(user=request.user).order_by('created_at')
        full_name = request.user.get_full_name() or request.user.username
    else:
        chat_sessions_qs = request.session.get('chat_sessions', [])
        full_name = None

    selected_chat_data = None
    if chat_id:
        if request.user.is_authenticated:
            selected_chat_obj = get_object_or_404(ChatSession, user=request.user, chat_id=chat_id)
            selected_chat_data = { # 템플릿에 일관된 형태로 전달하기 위함
                'chat_id': selected_chat_obj.chat_id,
                'initial_prompt': selected_chat_obj.initial_prompt,
                'history': selected_chat_obj.history
            }
        else:
            for session_item in chat_sessions_qs:
                if session_item['chat_id'] == chat_id:
                    selected_chat_data = session_item
                    break
    
    # style_list가 정의되어 있다고 가정합니다. (코드 상단에서 excel 파일 로드)
    recommended_styles = random.sample(style_list, min(len(style_list), 3)) if style_list else []


    return render(request, 'home.html', {
        'chat_sessions': chat_sessions_qs,
        'selected_chat': selected_chat_data,
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


@csrf_exempt
def save_final_prompt(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({'message': '비로그인 사용자는 저장할 수 없습니다.'}, status=403)

        data = json.loads(request.body)
        chat_id = data.get('chat_id')
        model_response = data.get('model_response')

        session = get_object_or_404(ChatSession, user=request.user, chat_id=chat_id)

        initial_prompt = session.initial_prompt
        if not initial_prompt:
            return JsonResponse({'message': '초기 프롬프트 없음'}, status=400)

        record = {
            "short_prompt": initial_prompt,
            "long_prompt": model_response
        }

        save_dir = os.path.join(settings.BASE_DIR, 'saved_prompts')
        os.makedirs(save_dir, exist_ok=True)

        save_path = os.path.join(save_dir, f"{request.user.id}_dataset.jsonl")

        with open(save_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        return JsonResponse({'message': '프롬프트 쌍이 파일에 저장되었습니다.'})

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



API_URL = "https://api-inference.huggingface.co/models/sdgsjlfnjkl/kanana-2.1b-full-v12"

HF_API_TOKEN = os.getenv("HF_API_TOKEN")

# API 요청 헤더 설정
if HF_API_TOKEN:
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
else:
    headers = {}
    print("!!! 경고: HF_API_TOKEN 환경 변수가 설정되지 않았습니다. API 호출에 제한이 있을 수 있습니다.")


# --- 2. API 호출 함수 정의 ---
def query_huggingface_api(prompt_text):
    """
    Hugging Face Inference API를 호출하여 모델 응답을 가져옵니다.
    """
    if not HF_API_TOKEN:
        print("API 토큰 없이 호출 시도...")
 
    payload = {
        "inputs": prompt_text,
        "parameters": {
            "max_new_tokens": 256,       
            "temperature": 0.7,         
            "top_p": 0.9,               
            "return_full_text": False,   
            # "repetition_penalty": 1.2, # 반복 패널티 (필요시)
        },
        "options": {
            "wait_for_model": True  
        }
    }

    try:
        print(f"Sending request to Hugging Face API: {API_URL}")
        # API 요청 보내기 (timeout 설정)
        response = requests.post(API_URL, headers=headers, json=payload, timeout=1000) 

        # HTTP 상태 코드 확인
        response.raise_for_status() # 200 OK 아니면 에러 발생

        # 응답 JSON 파싱
        result = response.json()
        print("Received response from API.")

        # 응답 구조 확인 및 결과 추출 
        if isinstance(result, list) and result and 'generated_text' in result[0]:
            return result[0]['generated_text'].strip()
        
        elif isinstance(result, dict) and 'generated_text' in result:
             return result['generated_text'].strip()
        
        else:
            print(f"Unexpected API response format: {result}")
            return "AI 모델 응답 형식 오류입니다. (관리자 문의)"

    except requests.exceptions.Timeout:
        print("Hugging Face API request timed out.")
        return "AI 모델 응답 시간이 초과되었습니다. 잠시 후 다시 시도해주세요."
    
    except requests.exceptions.RequestException as e:
        status_code = e.response.status_code if e.response is not None else 'N/A'
        error_message = str(e)
        print(f"Hugging Face API Error: {error_message} (Status Code: {status_code})")


        if status_code == 401: # Unauthorized
             return "오류: Hugging Face API 토큰이 유효하지 않습니다."
        
        elif status_code == 429: # Rate limit
             return "요청량이 많아 잠시 후 다시 시도해주세요. (API Rate Limit)"
        
        elif status_code == 503: # Model loading/unavailable
             return "AI 모델을 사용할 수 없습니다. 잠시 후 다시 시도해주세요. (503 Service Unavailable)"
       
        elif "read timeout" in error_message.lower():
             return "AI 모델 응답 시간이 초과되었습니다. (Read Timeout)"
      
        else:
             return f"AI 모델 API 오류가 발생했습니다. (코드: {status_code})"
   
    except json.JSONDecodeError:
        # API가 JSON이 아닌 다른 응답을 줄 경 
        print(f"Hugging Face API JSON Decode Error. Response text: {response.text[:200]}...") # 응답 내용 일부 확인
        return "AI 모델 응답 형식이 잘못되었습니다."
   
    except Exception as e:
         # 기타 예상치 못한 에러
         print(f"An unexpected error occurred during API query: {e}")
         return "AI 모델 처리 중 알 수 없는 오류가 발생했습니다."



def demo_qa_api(request):
    """
    데모용 API 뷰입니다.
    GET 요청으로 'question' 파라미터를 받아 DemoQA 모델에서 답변을 찾아 반환합니다.
    예: /api/demo_qa/?question=오늘 날씨 어때?
    """
    if request.method == 'GET':
        user_question = request.GET.get('question', None)

        if not user_question:
            return JsonResponse({'error': '질문(question) 파라미터가 필요합니다.'}, status=400)

        try:
            # DemoQA 모델에서 사용자의 질문과 일치하는 것을 찾습니다.
            # question__iexact는 대소문자를 구분하지 않고 일치하는 것을 찾습니다.
            # .strip()으로 앞뒤 공백을 제거해줍니다.
            demo_entry = DemoQA.objects.get(question__iexact=user_question.strip())
            response_data = {
                'question': demo_entry.question,
                'answer': demo_entry.answer,
                'category': demo_entry.category # 카테고리도 함께 반환 (선택 사항)
            }
            return JsonResponse(response_data)
        except DemoQA.DoesNotExist:
            # 해당 질문에 대한 데모 답변이 없는 경우
            return JsonResponse({
                'question': user_question,
                'answer': '죄송합니다, 이 질문에 대해서는 준비된 데모 답변이 없습니다.'
            }, status=404) # 404 Not Found
        except Exception as e:
            # 기타 예상치 못한 오류 처리
            # 실제 운영 환경에서는 오류 로깅을 하는 것이 좋습니다.
            print(f"Error in demo_qa_api: {e}")
            return JsonResponse({'error': '서버에서 오류가 발생했습니다.'}, status=500)
    else:
        # GET 요청이 아닌 경우
        return JsonResponse({'error': 'GET 요청만 지원합니다.'}, status=405) # 405 Method Not Allowed
