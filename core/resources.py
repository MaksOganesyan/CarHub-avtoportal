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

    # 1. фильтр только активных (для отчёта)
    def get_export_queryset(self):
        return self.Meta.model.objects.filter(status=self.Meta.model.ACTIVE)

    # 2 цена с форматированием (1 200 000 ₽ вместо 1200000)
    def dehydrate_price(self, car):
        return f"{int(car.price):,} ₽"

    # 3 статус вместо технического значения
    def dehydrate_status(self, car):
        if car.status == self.Meta.model.ACTIVE:
            return 'Активно'
        elif car.status == self.Meta.model.SOLD:
            return 'Продано'
        else:
            return 'На модерации'

    # 4 кастомное поле — имя продавца
    def dehydrate_user__username(self, car):
        if car.user:
            return car.user.username.upper()
        return '— (удалённый пользователь)'

    # 5: — короткое описание (первые 50 символов)
    def dehydrate_full_description(self, car):
        if car.description:
            return car.description[:50] + '...' if len(car.description) > 50 else car.description
        return 'Описание отсутствует'
