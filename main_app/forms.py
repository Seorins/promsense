from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class SignUpForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'password1', 'password2', 'email', 'full_name', 'birth_date', 'gender', 'address', 'address_detail']
        labels = {
            'username': '아이디',
            'password1': '비밀번호',
            'password2': '비밀번호 확인',
            'email': '이메일',
            'full_name': '이름',
            'birth_date': '생년월일',
            'gender': '성별',
            'address': '주소',
            'address_detail': '상세주소',
        }
        help_texts = {field: '' for field in fields}
        error_messages = {
            'username': {'required': '아이디를 입력해주세요.'},
            'password1': {'required': '비밀번호를 입력해주세요.'},
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.full_name = self.cleaned_data['full_name']
        user.birth_date = self.cleaned_data['birth_date']
        user.gender = self.cleaned_data['gender']
        user.address = self.cleaned_data['address']
        user.address_detail = self.cleaned_data['address_detail']
        if commit:
            user.save()
        return user


class EditProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['email', 'full_name', 'birth_date', 'gender', 'address', 'address_detail']
        labels = {
            'email': '이메일',
            'full_name': '이름',
            'birth_date': '생년월일',
            'gender': '성별',
            'address': '주소',
            'address_detail': '상세주소',
        }
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }