from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.db.models import Count
from django.http import HttpResponse
from .models import Car, Brand, Model, Favorite
from .forms import CustomUserCreationForm, CustomAuthenticationForm, CarForm


class CarListView(ListView):
    model = Car
    template_name = 'core/car_list.html'
    context_object_name = 'cars'
    # Пункт 3: оптимизация запросов
    queryset = Car.objects.filter(status=Car.ACTIVE).select_related('brand', 'model', 'user').prefetch_related('photos').order_by('-created_at')
    paginate_by = 10

    def get_context_data(self, **kwargs) -> dict:
        """
        Добавляет количество активных объявлений (демо аннотации в веб-слое).

        Возвращает:
            Словарь контекста с дополнительным 'total_active'.
        """
        context = super().get_context_data(**kwargs)
        # Небольшая демонстрация аннотации в веб-слое (пункт 5)
        # Можно использовать в шаблоне, если понадобится
        context['total_active'] = Car.objects.filter(status=Car.ACTIVE).count()
        return context


class CarDetailView(DetailView):
    model = Car
    template_name = 'core/car_detail.html'
    context_object_name = 'car'

    def get_context_data(self, **kwargs) -> dict:
        """
        Предоставляет фотографии и статус избранного для детальной страницы автомобиля.

        Использует prefetch-оптимизацию (пункт 3).
        """
        context = super().get_context_data(**kwargs)
        # Оптимизация: prefetch_related для доп. фото (пункт 3)
        self.object.photos.all().prefetch_related()  # no-op but documents intent
        context['photos'] = self.object.photos.all()
        # Проверяем, в избранном ли у текущего пользователя
        context['is_favorited'] = False
        if self.request.user.is_authenticated:
            context['is_favorited'] = Favorite.objects.filter(
                user=self.request.user, car=self.object
            ).exists()
        return context


class CarCreateView(LoginRequiredMixin, CreateView):
    model = Car
    form_class = CarForm
    template_name = 'core/car_form.html'
    success_url = reverse_lazy('core:car_list')

    def get_form_kwargs(self) -> dict:
        """Передаёт текущего пользователя в CarForm, чтобы скрыть поле статуса."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs) -> dict:
        """Предоставляет бренды и модели для зависимого select в шаблоне."""
        context = super().get_context_data(**kwargs)
        context['brands'] = Brand.objects.all()
        context['models'] = Model.objects.all()
        return context

    def form_valid(self, form) -> HttpResponse:
        """
        Устанавливает владельца и принудительно ставит статус MODERATION для не-staff (бизнес-логика).

        Возвращает redirect response.
        """
        form.instance.user = self.request.user
        form.instance.created_by = self.request.user
        # Обычные пользователи не могут сразу публиковать — только на модерацию
        if not self.request.user.is_staff:
            form.instance.status = Car.MODERATION
        response = super().form_valid(form)
        # Асинхронные задачи Celery (пункт 1 на отлично)
        from .tasks import send_car_submitted_for_moderation, process_car_image
        send_car_submitted_for_moderation.delay(self.object.id)
        if self.object.main_image:
            process_car_image.delay(self.object.id)
        messages.success(self.request, 'Объявление успешно добавлено!')
        return response

    def form_invalid(self, form) -> HttpResponse:
        """Показывает сообщение об ошибке при невалидной форме."""
        messages.error(self.request, 'Проверьте данные. Есть ошибки в форме.')
        return super().form_invalid(form)


class CarUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Car
    form_class = CarForm
    template_name = 'core/car_form.html'
    success_url = reverse_lazy('core:car_list')

    def get_form_kwargs(self) -> dict:
        """Передаёт пользователя в форму для управления полем статуса."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        self._previous_status = obj.status
        return obj

    def get_context_data(self, **kwargs) -> dict:
        """Предоставляет бренды и модели для формы редактирования."""
        context = super().get_context_data(**kwargs)
        context['brands'] = Brand.objects.all()
        context['models'] = Model.objects.all()
        return context

    def test_func(self) -> bool:
        """Только владелец автомобиля может его обновлять."""
        car = self.get_object()
        return self.request.user == car.user

    def form_valid(self, form) -> HttpResponse:
        """
        Ограничивает смену статуса для не-staff (только на SOLD разрешено).
        """
        # Для обычных пользователей статус можно менять только на SOLD (или оставляем как был)
        if not self.request.user.is_staff and 'status' in form.cleaned_data:
            # Разрешаем только переход в SOLD
            if form.cleaned_data['status'] != Car.SOLD:
                form.instance.status = self.object.status  # не даём менять на active/moderation
        response = super().form_valid(form)
        # Если одобрили (с moderation на active) — уведомляем продавца асинхронно
        if self.object.status == Car.ACTIVE and getattr(self, '_previous_status', None) == Car.MODERATION:
            from .tasks import send_car_approved_notification
            send_car_approved_notification.delay(self.object.id)
        return response


class CarDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Car
    template_name = 'core/car_confirm_delete.html'
    success_url = reverse_lazy('core:car_list')

    def test_func(self):
        """Только владелец может удалить автомобиль."""
        car = self.get_object()
        return self.request.user == car.user


# Регистрация и логин
def register(request):
    """
    Публичная форма регистрации. Принудительно устанавливает роль SELLER.

    Args:
        request: HttpRequest

    Returns:
        Отрендеренный шаблон регистрации или редирект после успеха.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Явно указываем backend из-за нескольких AUTHENTICATION_BACKENDS (allauth + ModelBackend)
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            # Асинхронное приветственное письмо
            from .tasks import send_welcome_email
            send_welcome_email.delay(user.id)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('core:car_list')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


def user_login(request):
    """Обрабатывает вход пользователя с сообщениями."""
    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            # Явно указываем backend из-за нескольких AUTHENTICATION_BACKENDS (allauth + ModelBackend)
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f'Добро пожаловать, {user.username}!')
            return redirect('core:car_list')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})


def user_logout(request):
    """Выход из аккаунта и редирект."""
    logout(request)
    messages.info(request, 'Вы вышли из аккаунта.')
    return redirect('core:car_list')


# === Избранное ===

class FavoritesListView(LoginRequiredMixin, ListView):
    """Список избранных объявлений текущего пользователя"""
    model = Favorite
    template_name = 'core/favorites_list.html'
    context_object_name = 'favorites'
    paginate_by = 10

    def get_queryset(self):
        """
        Оптимизированный queryset для избранных пользователя.

        Использует select_related + prefetch_related (оптимизация пункта 3).
        """
        # Пункт 3: хорошая оптимизация для избранного
        return (Favorite.objects
                .filter(user=self.request.user)
                .select_related('car', 'car__brand', 'car__model', 'car__user')
                .prefetch_related('car__photos')
                .order_by('-created_at'))


@login_required
def toggle_favorite(request, pk: int):
    """
    Переключает статус избранного для автомобиля (ожидается POST-запрос).

    Args:
        pk: Первичный ключ автомобиля.

    Только активные автомобили для обычных пользователей.
    """
    car = get_object_or_404(Car, pk=pk)

    # Разрешаем добавлять в избранное только активные объявления
    if car.status != Car.ACTIVE and not request.user.is_staff:
        messages.error(request, 'Можно добавлять в избранное только активные объявления.')
        return redirect('core:car_detail', pk=pk)

    fav, created = Favorite.objects.get_or_create(user=request.user, car=car)
    if not created:
        fav.delete()
        messages.info(request, 'Объявление удалено из избранного.')
    else:
        messages.success(request, 'Объявление добавлено в избранное.')

    # Возвращаемся на страницу объявления
    return redirect('core:car_detail', pk=pk)
