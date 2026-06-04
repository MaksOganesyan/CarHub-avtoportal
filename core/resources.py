from typing import Any

from django.db.models.query import QuerySet
from import_export import resources, fields

from .models import Car


class CarResource(resources.ModelResource):
    brand_name = fields.Field(attribute='brand__name', column_name='Марка автомобиля')
    model_name = fields.Field(attribute='model__name', column_name='Модель автомобиля')
    full_description = fields.Field(column_name='Краткое описание')
    year = fields.Field(attribute="year", column_name='Год')
    mileage = fields.Field(attribute='mileage', column_name="Пробег")
    price = fields.Field(attribute="price", column_name="Цена")
    status = fields.Field(attribute="status", column_name="Статус")
    user__username = fields.Field(attribute="user__username", column_name="Продавец")

    class Meta:
        model = Car
        fields = ('id', 'brand_name', 'model_name', 'year', 'mileage', 'price', 'full_description', 'status', 'user__username')
        export_order = ('id', 'brand_name', 'model_name', 'year', 'mileage', 'price', 'full_description', 'status')
        skip_unchanged = True
        report_skipped = False

    def get_export_queryset(self) -> QuerySet[Car]:
        """Возвращает queryset активных авто для отчётов экспорта."""
        return self.Meta.model.objects.filter(status=self.Meta.model.ACTIVE)

    def dehydrate_price(self, car: Car) -> str:
        """Возвращает отформатированную строку цены для экспорта."""
        return f"{int(car.price):,} ₽"

    def dehydrate_status(self, car: Car) -> str:
        """Возвращает читаемую метку статуса для экспорта."""
        if car.status == self.Meta.model.ACTIVE:
            return 'Активно'
        elif car.status == self.Meta.model.SOLD:
            return 'Продано'
        return 'На модерации'

    def dehydrate_user__username(self, car: Car) -> str:
        """Возвращает username продавца в UPPER для экспорта."""
        if car.user:
            return car.user.username.upper()
        return '— (удалённый пользователь)'

    def dehydrate_full_description(self, car: Car) -> str:
        """Возвращает укороченное описание для экспорта."""
        if car.description:
            return car.description[:50] + '...' if len(car.description) > 50 else car.description
        return 'Описание отсутствует'
