from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count, QuerySet
from .models import Car, Brand
from .serializers import CarSerializer, BrandSerializer
from .filters import CarFilter  # наш FilterSet


class IsSellerOrReadOnly(permissions.BasePermission):
    """
    Продавец может создавать/редактировать свои объявления.
    Остальные — только чтение (публичный доступ к активным).

    Модераторы и админы имеют расширенные права через отдельные действия и queryset логику.
    """

    def has_permission(self, request, view) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user or request.user.is_staff


class IsModeratorOrAdmin(permissions.BasePermission):
    """
    Только модераторы и админы могут выполнять действия модерации.
    Проверяет роль пользователя (moderator/admin) или is_staff.
    """

    def has_permission(self, request, view) -> bool:
        if not request.user.is_authenticated:
            return False
        if request.user.is_staff:
            return True
        role = getattr(request.user, 'role', None)
        return role in ('moderator', 'admin')


class CarViewSet(viewsets.ModelViewSet):
    """
    ViewSet для автомобилей (API).
    - Использует FilterSet (пункт 6 на удовлетворительно)
    - select_related + prefetch_related + annotate (пункт 3)
    - SerializerMethodField + context (пункт 4)
    - Ролевая авторизация

    Модераторы и админы (роль moderator/admin или is_staff) могут:
    - Видеть объявления на модерации (?moderation=1 или в get_queryset)
    - Использовать действия /approve/ и /reject/ (демонстрация ролей)
    """

    queryset = Car.objects.all().select_related('brand', 'model', 'user')
    serializer_class = CarSerializer
    filterset_class = CarFilter   # используем полноценный FilterSet

    permission_classes = [IsSellerOrReadOnly]

    search_fields = ['description', 'brand__name', 'model__name']
    ordering_fields = ['price', 'year', 'created_at', 'views']

    def get_queryset(self) -> QuerySet[Car]:
        """
        Базовый queryset с оптимизациями и кастомными фильтрами.

        - Обычные пользователи видят только ACTIVE.
        - Модераторы и админы (через роль или is_staff) могут видеть объявления на модерации.
        Применяет select_related, prefetch_related, annotations (photo_count)
        для демонстрации оптимизации запросов в DRF (через Silk).
        """
        user = getattr(self.request, 'user', None)
        is_moderator = bool(
            user and user.is_authenticated and (
                user.is_staff or getattr(user, 'role', None) in ('moderator', 'admin')
            )
        )

        if is_moderator:
            # Модераторы видят все объявления (или можно фильтровать по статусу)
            qs: QuerySet[Car] = Car.objects.all()
        else:
            qs: QuerySet[Car] = Car.objects.filter(status=Car.ACTIVE)

        if user and user.is_authenticated and 'my' in self.request.query_params:
            qs = qs.filter(user=user)

        if 'moderation' in self.request.query_params and is_moderator:
            qs = qs.filter(status=Car.MODERATION)

        if 'cheap_new_not_moderation' in self.request.query_params:
            qs = qs.filter(
                Q(price__lte=1500000) & Q(year__gte=2024) & ~Q(status=Car.MODERATION)
            )

        if 'old_or_expensive_not_sold' in self.request.query_params:
            qs = qs.filter(
                (Q(year__lt=2015) | Q(price__gt=3000000)) & ~Q(status=Car.SOLD)
            )

        return (
            qs.select_related('brand', 'model', 'user')
            .prefetch_related('photos')
            .annotate(photo_count=Count('photos'))
            .order_by('-created_at')
        )

    @action(detail=False, methods=['get'], url_path='cheap')
    def cheap(self, request) -> Response:
        """Кастомное действие: возвращает дешёвые автомобили (цена <= 1M). Для демо."""
        qs = self.get_queryset().filter(price__lte=1000000)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='view', permission_classes=[permissions.AllowAny])
    def view(self, request, pk=None) -> Response:
        """Кастомное действие для увеличения счётчика просмотров (без авторизации)."""
        car = self.get_object()
        car.views += 1
        car.save(update_fields=['views'])
        return Response({'message': 'Просмотр засчитан', 'views': car.views})

    @action(detail=True, methods=['post'], url_path='approve', permission_classes=[IsModeratorOrAdmin])
    def approve(self, request, pk=None) -> Response:
        """
        Одобрить объявление (модератор/админ переводит MODERATION -> ACTIVE).

        Отправляет уведомление продавцу через Celery.
        Доступно только пользователям с ролью moderator/admin или is_staff.
        """
        car = self.get_object()
        if car.status != Car.MODERATION:
            return Response({'error': 'Можно одобрять только объявления на модерации'}, status=400)
        car.status = Car.ACTIVE
        car.save(update_fields=['status'])
        from .tasks import send_car_approved_notification
        send_car_approved_notification.delay(car.id)
        return Response({'message': 'Объявление одобрено', 'status': car.status})

    @action(detail=True, methods=['post'], url_path='reject', permission_classes=[IsModeratorOrAdmin])
    def reject(self, request, pk=None) -> Response:
        """
        Отклонить объявление на модерации.

        Для демонстрации ролей: модератор может отклонить (здесь удаляем для простоты).
        В реальной системе можно менять статус на rejected или оставлять с комментарием.
        Доступно только модераторам и админам.
        """
        car = self.get_object()
        if car.status != Car.MODERATION:
            return Response({'error': 'Можно отклонять только объявления на модерации'}, status=400)
        car_id = car.id
        car.delete()
        return Response({'message': f'Объявление #{car_id} отклонено и удалено'})


class BrandViewSet(viewsets.ModelViewSet):
    """API для Brands. Простой CRUD с поиском/сортировкой."""

    queryset = Brand.objects.all().order_by('name')
    serializer_class = BrandSerializer
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
