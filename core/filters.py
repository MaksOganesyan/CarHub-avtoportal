import django_filters
from django.db.models import Q
from .models import Car, Brand, Model


class CarFilter(django_filters.FilterSet):
    """
    Полноценный FilterSet для объявлений (удовлетворяет пункту 6 задания grade3 / grade4).

    Поддерживает:
    - Фильтр по бренду и модели
    - Диапазон цены (price_min / price_max)
    - Диапазон года (year_min / year_max)
    - Статус
    - Быстрый текстовый поиск q=
    """
    brand = django_filters.ModelChoiceFilter(
        queryset=Brand.objects.all(),
        label='Марка'
    )
    model = django_filters.ModelChoiceFilter(
        queryset=Model.objects.all(),
        label='Модель'
    )

    price_min = django_filters.NumberFilter(field_name='price', lookup_expr='gte', label='Цена от')
    price_max = django_filters.NumberFilter(field_name='price', lookup_expr='lte', label='Цена до')

    year_min = django_filters.NumberFilter(field_name='year', lookup_expr='gte', label='Год от')
    year_max = django_filters.NumberFilter(field_name='year', lookup_expr='lte', label='Год до')

    q = django_filters.CharFilter(method='filter_search', label='Поиск')

    class Meta:
        model = Car
        fields = {
            'status': ['exact'],
            'brand': ['exact'],
            'model': ['exact'],
        }

    def filter_search(self, queryset, name: str, value: str):
        """Кастомный поисковый фильтр по описанию/названию бренда/модели."""
        if not value:
            return queryset
        return queryset.filter(
            Q(description__icontains=value) |
            Q(brand__name__icontains=value) |
            Q(model__name__icontains=value)
        )