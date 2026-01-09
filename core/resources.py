from import_export import resources
from .models import Car


class CarResource(resources.ModelResource):
    class Meta:
        model = Car
        fields = ('id', 'brand', 'model', 'year', 'mileage', 'price', 'description', 'status', 'user__username')
