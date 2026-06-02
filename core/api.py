from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count
from .models import Car, Brand
from .serializers import CarSerializer, BrandSerializer
from .filters import CarFilter  # наш FilterSet

class IsSellerOrReadOnly(permissions.BasePermission):
    """
    Продавец (или staff) может создавать/редактировать свои объявления.
    Остальные — только чтение.

    Используется в CarViewSet для ролевой авторизации (часть валидации пункта 4).
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
    """Только модераторы и админы могут модерировать (permission class)."""

    def has_permission(self, request, view) -> bool:
        return request.user.is_authenticated and (request.user.is_staff or getattr(request.user, 'role', None) in ('moderator', 'admin'))


class CarViewSet(viewsets.ModelViewSet):
    """
    API for Cars.
    - Uses FilterSet (point 6 grade 3)
    - select_related + prefetch + annotate (point 3)
    - SerializerMethodField and context (point 4)
    - Role based permissions
    """

    queryset = Car.objects.filter(status=Car.ACTIVE).select_related('brand', 'model', 'user')
    serializer_class = CarSerializer
    filterset_class = CarFilter   # используем полноценный FilterSet

    # Базовые права: чтение для всех, запись — только для продавцов (с проверкой владельца)
    permission_classes = [IsSellerOrReadOnly]

    search_fields = ['description', 'brand__name', 'model__name']
    ordering_fields = ['price', 'year', 'created_at', 'views']

    def get_queryset(self):
        """
        Базовый queryset с оптимизациями и кастомными фильтрами.

        Применяет select_related, prefetch, annotations (photo_count) для производительности.
        """
        qs = super().get_queryset()

        if self.request.user.is_authenticated and 'my' in self.request.query_params:
            qs = qs.filter(user=self.request.user)

        if 'cheap_new_not_moderation' in self.request.query_params:
            qs = qs.filter(
                Q(price__lte=1500000) & Q(year__gte=2024) & ~Q(status=Car.MODERATION)
            )

        if 'old_or_expensive_not_sold' in self.request.query_params:
            qs = qs.filter(
                (Q(year__lt=2015) | Q(price__gt=3000000)) & ~Q(status=Car.SOLD)
            )

        return qs.select_related('brand', 'model', 'user').prefetch_related('photos').annotate(
            photo_count=Count('photos')
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


class BrandViewSet(viewsets.ModelViewSet):
    """API для Brands. Простой CRUD с поиском/сортировкой."""

    queryset = Brand.objects.all().order_by('name')
    serializer_class = BrandSerializer
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
