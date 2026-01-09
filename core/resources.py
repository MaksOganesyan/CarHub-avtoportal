from import_export import resources, fields
from .models import Car

class CarResource(resources.ModelResource):
    id = fields.Field(attribute='id', column_name='ID')
    brand_name = fields.Field(attribute='brand__name', column_name='Марка автомобиля')
    model_name = fields.Field(attribute='model__name', column_name='Модель автомобиля')
    year = fields.Field(attribute='year', column_name='Год выпуска')
    mileage = fields.Field(attribute='mileage', column_name='Пробег, км')
    price = fields.Field(attribute='price', column_name='Цена, ₽')
    description = fields.Field(attribute='description', column_name='Описание')
    status = fields.Field(attribute='status', column_name='Статус объявления')
    user_username = fields.Field(attribute='user__username', column_name='Продавец')

    class Meta:
        model = Car
        fields = ('id', 'brand_name', 'model_name', 'year', 'mileage', 'price', 'description', 'status', 'user_username')
        export_order = fields

    def get_export_queryset(self):
        return self.Meta.model.objects.filter(status='active')
