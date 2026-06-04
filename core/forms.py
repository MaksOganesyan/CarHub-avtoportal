from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Car


class CustomUserCreationForm(UserCreationForm):
    """
    Кастомная форма регистрации.

    При сохранении всегда форсирует роль SELLER (бизнес-правило).
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

    def __init__(self, *args, **kwargs) -> None:
        """Устанавливает русские лейблы и подсказки для полей паролей."""
        super().__init__(*args, **kwargs)
        if 'password1' in self.fields:
            self.fields['password1'].label = 'Пароль'
            self.fields['password1'].help_text = 'Пароль должен содержать минимум 8 символов. Не используйте слишком простые пароли.'
        if 'password2' in self.fields:
            self.fields['password2'].label = 'Подтверждение пароля'
            self.fields['password2'].help_text = 'Введите тот же пароль ещё раз для подтверждения.'

    def save(self, commit: bool = True) -> User:
        """
        Сохраняет пользователя и принудительно устанавливает роль SELLER при публичной регистрации.
        """
        user = super().save(commit=False)
        user.role = User.SELLER
        if commit:
            user.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    """Кастомная форма входа (можно расширять полями в будущем)."""
    pass


class CarForm(forms.ModelForm):
    """
    Форма для создания/редактирования объявлений об автомобилях.

    Скрывает поле статуса для не-staff пользователей (продавцов).
    Статус принудительно устанавливается во view/serializer (moderation при создании).
    """

    class Meta:
        model = Car
        fields = [
            'brand', 'model', 'year', 'mileage', 'price',
            'description', 'main_image', 'main_image_url', 'status'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    def __init__(self, *args, **kwargs) -> None:
        """
        Инициализирует форму и убирает поле статуса для обычных пользователей (продавцов).

        Статус могут видеть и менять staff, модераторы и админы (для одобрения объявлений).
        """
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        is_privileged = user and (user.is_staff or getattr(user, 'role', None) in ('moderator', 'admin'))
        if user and not is_privileged:
            self.fields.pop('status', None)
