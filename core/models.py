from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords


class User(AbstractUser):
    """
    Кастомная модель пользователя с ролями (user/seller/moderator/admin).

    Роль SELLER принудительно выдаётся при регистрации и через сигналы allauth (OAuth).
    """

    USER = 'user'
    SELLER = 'seller'
    MODERATOR = 'moderator'
    ADMIN = 'admin'

    ROLE_CHOICES = (
        (USER, _('Обычный пользователь')),
        (SELLER, _('Продавец')),
        (MODERATOR, _('Модератор')),
        (ADMIN, _('Администратор')),
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=SELLER,
        verbose_name=_('Роль')
    )
    phone = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        verbose_name=_('Телефон')
    )
    last_login = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Последний вход')
    )

    class Meta:
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')

    def __str__(self) -> str:
        """Возвращает человекочитаемое представление пользователя."""
        return self.get_full_name() or self.username


class Brand(models.Model):
    """Справочник марок автомобилей (Brand)."""

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Название марки')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )

    class Meta:
        verbose_name = _('Марка автомобиля')
        verbose_name_plural = _('Марки автомобилей')
        ordering = ['name']

    def __str__(self) -> str:
        """Возвращает название марки."""
        return self.name


class Model(models.Model):
    """Модель автомобиля (принадлежит Brand)."""

    brand = models.ForeignKey(
        Brand,
        on_delete=models.CASCADE,
        related_name='models',
        verbose_name=_('Марка')
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_('Название модели')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )

    class Meta:
        verbose_name = _('Модель автомобиля')
        verbose_name_plural = _('Модели автомобилей')
        unique_together = ('brand', 'name')
        ordering = ['name']

    def __str__(self) -> str:
        """Возвращает название модели."""
        return self.name


class Car(models.Model):
    """
    Основная модель объявления об автомобиле.

    Содержит статусы (MODERATION / ACTIVE / SOLD), бизнес-логику через views/serializers.
    Использует select_related везде для оптимизации.
    """

    MODERATION = 'moderation'
    ACTIVE = 'active'
    SOLD = 'sold'

    STATUS_CHOICES = (
        (MODERATION, _('На модерации')),
        (ACTIVE, _('Активно')),
        (SOLD, _('Продано')),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cars',
        verbose_name=_('Продавец')
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        verbose_name=_('Марка')
    )
    model = models.ForeignKey(
        Model,
        on_delete=models.PROTECT,
        verbose_name=_('Модель')
    )
    year = models.PositiveIntegerField(
        verbose_name=_('Год выпуска')
    )
    mileage = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_('Пробег, км')
    )
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_('Цена')
    )
    description = models.TextField(
        verbose_name=_('Описание')
    )
    main_image_url = models.URLField(
        max_length=255,
        blank=True,
        verbose_name=_('Основное фото (URL)')
    )
    main_image = models.ImageField(
        upload_to='cars/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name='Главное фото'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='moderation',
        verbose_name=_('Статус объявления')
    )
    views = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Количество просмотров')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_cars',
        verbose_name=_('Кем создано')
    )
    history = HistoricalRecords()

    class Meta:
        verbose_name = _('Объявление об автомобиле')
        verbose_name_plural = _('Объявления об автомобилях')
        ordering = ['-created_at']

    def __str__(self) -> str:
        """Возвращает краткое описание объявления об автомобиле."""
        return f'{self.model} ({self.year}) - {self.price} ₽'


class CarPhoto(models.Model):
    """Дополнительные фотографии к объявлению Car (однонаправленный FK)."""

    car = models.ForeignKey(
        Car,
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name=_('Автомобиль')
    )
    image_url = models.URLField(
        max_length=255,
        verbose_name=_('URL фотографии')
    )
    is_main = models.BooleanField(
        default=False,
        verbose_name=_('Основное фото')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата загрузки')
    )

    class Meta:
        verbose_name = _('Фотография автомобиля')
        verbose_name_plural = _('Фотографии автомобилей')

    def __str__(self) -> str:
        """Возвращает описание фотографии."""
        return f'Фото для {self.car} ({self.created_at.date()})'


class Favorite(models.Model):
    """Связь «пользователь — избранное объявление» (многие-ко-многим через модель)."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name=_('Пользователь')
    )
    car = models.ForeignKey(
        Car,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name=_('Объявление')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата добавления')
    )

    class Meta:
        verbose_name = _('Избранное объявление')
        verbose_name_plural = _('Избранные объявления')
        unique_together = ('user', 'car')

    def __str__(self) -> str:
        """Возвращает представление избранного."""
        return f'{self.user} ♥ {self.car}'
