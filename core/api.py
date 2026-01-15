from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Car, Brand
from .serializers import CarSerializer, BrandSerializer


# Api объявления
class CarViewSet(viewsets.ModelViewSet):
    queryset = Car.objects.filter(status='active').select_related('brand', 'model', 'user')
    serializer_class = CarSerializer

    filterset_fields = ['brand', 'model', 'year', 'status', 'price']
    search_fields = ['description', 'brand__name', 'model__name']
    ordering_fields = ['price', 'year', 'created_at', 'views']

    def get_queryset(self):
        qs = super().get_queryset()

        # собственные объявления
        if self.request.user.is_authenticated and 'my' in self.request.query_params:
            qs = qs.filter(user=self.request.user)

        # Запрос 1:
        if 'cheap_new_not_moderation' in self.request.query_params:
            qs = qs.filter(
                Q(price__lte=1500000) & Q(year__gte=2024) & ~Q(status='moderation')
            )

        # Запрос 2
        if 'old_or_expensive_not_sold' in self.request.query_params:
            qs = qs.filter(
                (Q(year__lt=2015) | Q(price__gt=3000000)) & ~Q(status='sold')
            )

        return qs

    # Дешёвые тачки GET /api/cars/cheap/
    @action(detail=False, methods=['get'])
    def cheap(self, request):
        qs = self.get_queryset().filter(price__lte=1000000)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    # Увеличить просмотры POST /api/cars/{id}/view/
    @action(detail=True, methods=['post'])
    def view(self, request, pk=None):
        car = self.get_object()
        car.views += 1
        car.save(update_fields=['views'])
        return Response({'message': 'Просмотр засчитан', 'views': car.views})


#  API для марок автомобилей api/brands/
class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all().order_by('name')
    serializer_class = BrandSerializer
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
