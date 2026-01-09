from rest_framework import serializers
from .models import Car, Brand, Model


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'created_at']
        read_only_fields = ['created_at']

    def validate_name(self, value):
        if Brand.objects.filter(name__iexact=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("Марка с таким названием уже существует")
        return value


class CarSerializer(serializers.ModelSerializer):
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    model_name = serializers.CharField(source='model.name', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)

    brand = serializers.PrimaryKeyRelatedField(
        queryset=Brand.objects.all(),
        required=True,
        write_only=True
    )
    model = serializers.PrimaryKeyRelatedField(
        queryset=Model.objects.all(),
        required=True,
        write_only=True
    )

    class Meta:
        model = Car
        fields = [
            'id', 'brand', 'brand_name', 'model', 'model_name',
            'year', 'mileage', 'price', 'description', 'main_image_url',
            'status', 'views', 'user', 'user_name', 'created_at'
        ]
        read_only_fields = ['views', 'created_at', 'user', 'user_name']

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Цена не может быть отрицательной")
        if value == 0:
            raise serializers.ValidationError("Цена должна быть больше 0")
        return value

    def validate_year(self, value):
        current_year = 2026
        if value < 1900:
            raise serializers.ValidationError("Год не может быть раньше 1900")
        if value > current_year + 1:
            raise serializers.ValidationError(f"Год не может быть позже {current_year + 1}")
        return value

    def validate(self, data):
        brand = data.get('brand')
        model = data.get('model')
        if brand and model and model.brand != brand:
            raise serializers.ValidationError({"model": "Модель не принадлежит выбранной марке"})
        return data

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
