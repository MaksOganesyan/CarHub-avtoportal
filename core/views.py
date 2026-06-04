from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.http import HttpResponse
from .models import Car, Brand, Model, Favorite
from .forms import CustomUserCreationForm, CustomAuthenticationForm, CarForm


class LightweightPage:
    """Минимальный объект страницы для пагинации без COUNT-запроса."""

    def __init__(self, number: int, has_next: bool) -> None:
        """Имитирует django.core.paginator.Page для кастомной пагинации без COUNT."""
        self.number = number
        self._has_next = has_next

    def has_previous(self) -> bool:
        """Есть ли предыдущая страница."""
        return self.number > 1

    def has_next(self) -> bool:
        """Есть ли следующая страница (определяется по наличию +1 элемента)."""
        return self._has_next

    def previous_page_number(self) -> int:
        """Номер предыдущей страницы."""
        return max(self.number - 1, 1)

    def next_page_number(self) -> int:
        """Номер следующей страницы."""
        return self.number + 1


class CarListView(ListView):
    """
    Список активных объявлений.

    Оптимизация запросов (пункт для оценки):
    - select_related('brand', 'model', 'user') — избегаем N+1 при выводе марки/модели/продавца в шаблоне.
    - Кастомная пагинация без COUNT (берём page_size+1) для демонстрации через Silk/toolbar.
    """
    model = Car
    template_name = 'core/car_list.html'
    context_object_name = 'cars'
    page_size = 6

    def get_queryset(self):
        """Возвращает оптимизированный queryset только активных авто с подгрузкой связанных объектов."""
        return (
            Car.objects.filter(status=Car.ACTIVE)
            .select_related('brand', 'model', 'user')
            .order_by('-created_at')
        )

    def get_context_data(self, **kwargs) -> dict:
        """Добавляет пагинацию без COUNT-запроса: берём на один объект больше для has_next."""
        # self.object_list уже содержит результаты get_queryset (с select_related)
        page_number = self._get_page_number()
        offset = (page_number - 1) * self.page_size
        items = list(self.object_list[offset:offset + self.page_size + 1])
        cars = items[:self.page_size]
        page_obj = LightweightPage(page_number, len(items) > self.page_size)

        context = {
            'cars': cars,
            'object_list': cars,
            'page_obj': page_obj,
            'is_paginated': page_obj.has_previous() or page_obj.has_next(),
            'view': self,
        }
        context.update(kwargs)
        return context

    def _get_page_number(self) -> int:
        """Возвращает номер страницы из query params, защищаясь от мусорных значений."""
        try:
            return max(int(self.request.GET.get('page', 1)), 1)
        except (TypeError, ValueError):
            return 1


class CarDetailView(DetailView):
    """
    Детальная страница объявления.

    Оптимизация:
    - select_related для brand/model/user
    - prefetch_related('photos') — одна запрос на все фото вместо N
    """
    model = Car
    template_name = 'core/car_detail.html'
    context_object_name = 'car'

    def get_queryset(self):
        """Оптимизированный queryset с подгрузкой связанных объектов и фотографий."""
        return (
            super().get_queryset()
            .select_related('brand', 'model', 'user')
            .prefetch_related('photos')
        )

    def get_context_data(self, **kwargs) -> dict:
        """
        Предоставляет фотографии (из prefetch) и статус избранного текущего пользователя.
        """
        context = super().get_context_data(**kwargs)
        # После prefetch_related обращение не вызывает дополнительных запросов
        context['photos'] = self.object.photos.all()
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
        context['models'] = Model.objects.select_related('brand').all()
        return context

    def form_valid(self, form) -> HttpResponse:
        """
        Устанавливает владельца и принудительно ставит статус MODERATION для не-staff (бизнес-логика).

        Возвращает redirect response.
        """
        form.instance.user = self.request.user
        form.instance.created_by = self.request.user
        if not self.request.user.is_staff:
            form.instance.status = Car.MODERATION
        response = super().form_valid(form)
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
        """Получает объект и запоминает предыдущий статус (для проверки перехода MODERATION -> ACTIVE)."""
        obj = super().get_object(queryset)
        self._previous_status = obj.status
        return obj

    def get_context_data(self, **kwargs) -> dict:
        """Предоставляет бренды и модели для формы редактирования."""
        context = super().get_context_data(**kwargs)
        context['brands'] = Brand.objects.all()
        context['models'] = Model.objects.select_related('brand').all()
        return context

    def test_func(self) -> bool:
        """Только владелец автомобиля может его обновлять."""
        car = self.get_object()
        return self.request.user == car.user

    def form_valid(self, form) -> HttpResponse:
        """
        Ограничивает смену статуса для не-staff (только на SOLD разрешено).
        """
        if not self.request.user.is_staff and 'status' in form.cleaned_data:
            if form.cleaned_data['status'] != Car.SOLD:
                form.instance.status = self.object.status
        response = super().form_valid(form)
        if self.object.status == Car.ACTIVE and getattr(self, '_previous_status', None) == Car.MODERATION:
            from .tasks import send_car_approved_notification
            send_car_approved_notification.delay(self.object.id)
        return response


class CarDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Car
    template_name = 'core/car_confirm_delete.html'
    success_url = reverse_lazy('core:car_list')

    def test_func(self) -> bool:
        """Только владелец может удалить автомобиль."""
        car = self.get_object()
        return self.request.user == car.user


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
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            from .tasks import send_welcome_email
            send_welcome_email.delay(user.id)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('core:car_list')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


def user_login(request):
    """
    Обрабатывает аутентификацию пользователя.

    Args:
        request: HttpRequest

    Returns:
        Редирект на список авто при успехе или рендер формы логина.
    """
    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f'Добро пожаловать, {user.username}!')
            return redirect('core:car_list')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})


def user_logout(request):
    """
    Выполняет выход пользователя из системы.

    Args:
        request: HttpRequest

    Returns:
        Редирект на главную страницу.
    """
    logout(request)
    messages.info(request, 'Вы вышли из аккаунта.')
    return redirect('core:car_list')


class FavoritesListView(LoginRequiredMixin, ListView):
    """
    Список избранных объявлений текущего пользователя.

    Оптимизация запросов:
    - select_related по цепочке car__brand, car__model, car__user (избегаем 4 N+1)
    - prefetch_related('car__photos')
    """
    model = Favorite
    template_name = 'core/favorites_list.html'
    context_object_name = 'favorites'
    paginate_by = 10

    def get_queryset(self):
        """Оптимизированный queryset избранного с глубоким select_related + prefetch фото."""
        return (
            Favorite.objects
            .filter(user=self.request.user)
            .select_related('car', 'car__brand', 'car__model', 'car__user')
            .prefetch_related('car__photos')
            .order_by('-created_at')
        )


@login_required
def toggle_favorite(request, pk: int) -> HttpResponse:
    """
    Переключает статус избранного для автомобиля (ожидается POST-запрос).

    Args:
        pk: Первичный ключ автомобиля.

    Returns:
        Редирект обратно на страницу детали автомобиля.
    """
    car = get_object_or_404(Car, pk=pk)

    if car.status != Car.ACTIVE and not request.user.is_staff:
        messages.error(request, 'Можно добавлять в избранное только активные объявления.')
        return redirect('core:car_detail', pk=pk)

    fav, created = Favorite.objects.get_or_create(user=request.user, car=car)
    if not created:
        fav.delete()
        messages.info(request, 'Объявление удалено из избранного.')
    else:
        messages.success(request, 'Объявление добавлено в избранное.')

    return redirect('core:car_detail', pk=pk)


import logging

logger = logging.getLogger(__name__)


def handler404(request, exception):
    """
    Кастомный обработчик 404 для продакшена.

    Всегда отправляет информацию о 404 в GlitchTip (capture_message),
    чтобы ошибки отсутствующих страниц были видны в дашборде (для демонстрации на защите).
    Возвращает простой ответ (шаблон 404.html будет использован фреймворком при DEBUG=False).
    """
    path = request.path
    method = request.method
    msg = f"404 Not Found: {path} (method={method})"
    logger.warning(msg)
    try:
        import sentry_sdk
        sentry_sdk.capture_message(msg, level="error")
    except Exception:
        pass  # не роняем 404 если SDK не готов
    from django.shortcuts import render
    # Возвращаем красивый, но минимальный 404 (templates/404.html) — без debug-трассировок при DEBUG=False
    return render(request, '404.html', status=404)


def trigger_glitchtip_error(request):
    """
    Специальный view для демонстрации работы GlitchTip на защите курсовой.

    При обращении к /trigger-glitchtip-error/ намеренно вызывает исключение.
    Это гарантированно отправит ошибку в облачный GlitchTip (через DjangoIntegration),
    даже если обычные 404 по каким-то причинам не доходят.
    Используйте во время показа: откройте этот URL в браузере — ошибка появится в дашборде GlitchTip.

    В реальном продакшене этот эндпоинт можно отключить или защитить.
    """
    # Разные типы для демонстрации: деление на ноль + явный capture
    try:
        _ = 1 / 0
    except ZeroDivisionError as exc:
        logger.error("Demo error triggered for GlitchTip: division by zero")
        try:
            import sentry_sdk
            sentry_sdk.capture_exception(exc)
            # Также отправим кастомное сообщение
            sentry_sdk.capture_message("GlitchTip demo: trigger_glitchtip_error executed in prod (CarHub)", level="error")
        except Exception:
            pass
        raise  # даём исключению подняться, чтобы DjangoIntegration тоже поймал
