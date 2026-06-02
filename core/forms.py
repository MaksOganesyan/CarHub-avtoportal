from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Car


class CustomUserCreationForm(UserCreationForm):
    """
    Форма регистрации.
    - Роль не показывается обычному пользователю.
    - При публичной регистрации всегда присваивается роль 'seller' (Продавец).
    - Админ и модератор могут назначаться только суперпользователем через админку.
    - Все подсказки и лейблы на русском.
    """
    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'password1', 'password2')
        labels = {
            'username': 'Имя пользователя',
            'email': 'Email',
            'phone': 'Телефон',
        }
        help_texts = {
            'username': 'Только буквы, цифры и символы @ . + - _ .',
            'email': 'Укажите действующий email.',
            'phone': 'В формате +7 (XXX) XXX-XX-XX или без форматирования.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Русские лейблы и подсказки для паролей (они не в Meta, т.к. от родителя)
        if 'password1' in self.fields:
            self.fields['password1'].label = 'Пароль'
            self.fields['password1'].help_text = 'Пароль должен содержать минимум 8 символов. Не используйте слишком простые пароли.'
        if 'password2' in self.fields:
            self.fields['password2'].label = 'Подтверждение пароля'
            self.fields['password2'].help_text = 'Введите тот же пароль ещё раз для подтверждения.'

    def save(self, commit=True):
        user = super().save(commit=False)
        # Публичная регистрация → всегда продавец.
        # "Обычный пользователь" (buyer) здесь не выбирается.
        # Админ/модератор назначаются только через админ-панель суперпользователем.
        user.role = User.SELLER
        if commit:
            user.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    class Meta:
        model = User


class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = [
            'brand', 'model', 'year', 'mileage', 'price',
            'description', 'main_image', 'main_image_url', 'status'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Обычным пользователям не даём выбирать статус в форме
        if user and not user.is_staff:
            self.fields.pop('status', None)
