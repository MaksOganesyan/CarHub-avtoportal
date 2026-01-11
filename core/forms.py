from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Car

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'role', 'password1', 'password2')


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
