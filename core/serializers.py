from rest_framework import serializers
from .models import Car, Brand, Model, CarPhoto


class BrandSerializer(serializers.ModelSerializer):
    """Сериализатор для Brand с валидацией уникальности названия."""

    class Meta:
        model = Brand
        fields = ['id', 'name', 'created_at']
        read_only_fields = ['created_at']

    def validate_name(self, value: str) -> str:
        if Brand.objects.filter(name__iexact=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("Марка с таким названием уже существует")
        return value


class CarSerializer(serializers.ModelSerializer):
    """
    Сериализатор для Car с:
    - SerializerMethodField для вычисляемых полей (photo_count, main_photo, is_favorited через context)
    - Использование context для данных, специфичных для пользователя
    - Валидация бизнес-логики
    """

    brand_name = serializers.CharField(source='brand.name', read_only=True)
    model_name = serializers.CharField(source='model.name', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)

    # === Пункт 4.1 задания: SerializerMethodField ===
    photo_count = serializers.SerializerMethodField()
    main_photo = serializers.SerializerMethodField()

    # === Пункт 4.2: данные через context (is_favorited для текущего пользователя) ===
    is_favorited = serializers.SerializerMethodField()

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
            'status', 'views', 'user', 'user_name', 'created_at',
            'photo_count', 'main_photo', 'is_favorited'
        ]
        read_only_fields = ['views', 'created_at', 'user', 'user_name', 'photo_count', 'main_photo', 'is_favorited']

    # === SerializerMethodField примеры ===

    def get_photo_count(self, obj: Car) -> int:
        """Количество дополнительных фотографий у объявления (SerializerMethodField)."""
        return obj.photos.count()

    def get_main_photo(self, obj: Car) -> str | None:
        """Возвращает URL главного фото (приоритет: загруженное > внешняя ссылка)."""
        if obj.main_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.main_image.url)
            return obj.main_image.url
        return obj.main_image_url or None

    def get_is_favorited(self, obj: Car) -> bool:
        """
        Пункт 4.2 задания: используем context (request.user) чтобы определить,
        находится ли объявление в избранном у текущего пользователя.
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        # Избегаем лишнего запроса, если related_name уже загружен (через prefetch)
        if hasattr(obj, '_favorited_by_user_ids'):
            return request.user.id in obj._favorited_by_user_ids
        return obj.favorited_by.filter(user=request.user).exists()

    # === Валидация бизнес-логики (пункт 2) ===

    def validate_price(self, value: float) -> float:
        """Валидирует, что цена > 0."""
        if value < 0:
            raise serializers.ValidationError("Цена не может быть отрицательной")
        if value == 0:
            raise serializers.ValidationError("Цена должна быть больше 0")
        return value

    def validate_year(self, value: int) -> int:
        """Валидирует разумность года выпуска."""
        current_year = 2026
        if value < 1900:
            raise serializers.ValidationError("Год не может быть раньше 1900")
        if value > current_year + 1:
            raise serializers.ValidationError(f"Год не может быть позже {current_year + 1}")
        return value

    def validate(self, data: dict) -> dict:
        """Кросс-валидация: модель должна принадлежать бренду."""
        brand = data.get('brand')
        model = data.get('model')
        if brand and model and model.brand != brand:
            raise serializers.ValidationError({"model": "Модель не принадлежит выбранной марке"})
        return data

    def create(self, validated_data: dict) -> Car:
        """
        Create car and force MODERATION for non-staff users.

        Uses context to get the authenticated user.
        """
        validated_data['user'] = self.context['request'].user
        # Обычные пользователи не могут сразу публиковать
        if not self.context['request'].user.is_staff:
            validated_data['status'] = Car.MODERATION
        return super().create(validated_data)
