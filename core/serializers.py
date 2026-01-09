from rest_framework import serializers
from .models import Car


class CarSerializer(serializers.ModelSerializer):
    brand = serializers.StringRelatedField()
    model = serializers.StringRelatedField()
    user = serializers.StringRelatedField()

    class Meta:
        model = Car
        fields = ['id', 'brand', 'model', 'year', 'mileage', 'price', 'description', 'main_image_url', 'status', 'views', 'user']

    # Пример своей валидации
    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Цена не может быть отрицательной")
        return value
