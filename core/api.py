from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Car
from .serializers import CarSerializer


class CarViewSet(viewsets.ModelViewSet):
    queryset = Car.objects.filter(status='active').select_related('brand', 'model', 'user')
    serializer_class = CarSerializer
    filterset_fields = ['brand', 'model', 'year']  # фильтр по get-параметрам
    search_fields = ['description', 'brand__name', 'model__name']  # поиск
    ordering_fields = ['price', 'year', 'created_at']

    # Фильтр: только свои объявления для аутентифицированного пользователя
    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_authenticated:
            if 'my' in self.request.query_params:
                qs = qs.filter(user=self.request.user)
        return qs

    # Дополнительный метод для списка
    @action(detail=False, methods=['get'])
    def cheap(self, request):
        qs = self.get_queryset().filter(price__lt=1000000)  # пример: дешевле миллиона
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    # Дополнительный метод для объекта (например, отметить просмотренным)
    @action(detail=True, methods=['post'])
    def view(self, request, pk=None):
        car = self.get_object()
        car.views += 1
        car.save()
        return Response({'views': car.views})
