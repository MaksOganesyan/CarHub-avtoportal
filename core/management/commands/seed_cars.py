from decimal import Decimal
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError

from core.models import Brand, Car, Model, User


class Command(BaseCommand):
    """Создаёт демонстрационные объявления с локальными фото из docs/img."""

    help = 'Создаёт 10 активных объявлений CarHub с корректными изображениями.'

    def handle(self, *args: Any, **options: Any) -> None:
        """Выполняет наполнение базы демонстрационными объявлениями."""
        image_dir = settings.BASE_DIR / 'docs' / 'img'
        if not image_dir.exists():
            raise CommandError(f'Папка с изображениями не найдена: {image_dir}')

        seller = self._get_seller()
        created_count = 0
        updated_count = 0

        for item in self._seed_data():
            image_path = image_dir / item['image']
            if not image_path.exists():
                raise CommandError(f'Изображение не найдено: {image_path}')

            brand = self._get_brand(item['brand'])
            model = self._get_model(brand, item['model'])
            seed_code = f"[seed:{item['code']}]"

            car = Car.objects.filter(description__contains=seed_code).first()
            if car is None:
                car = Car(user=seller, created_by=seller)
                created_count += 1
            else:
                updated_count += 1

            car.user = seller
            car.created_by = seller
            car.brand = brand
            car.model = model
            car.year = item['year']
            car.mileage = item['mileage']
            car.price = Decimal(item['price'])
            car.status = Car.ACTIVE
            car.views = item['views']
            car.description = f"{item['description']}\n\n{seed_code}"
            car.main_image_url = ''

            self._attach_image(car, image_path, item['code'])
            car.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'Готово: создано {created_count}, обновлено {updated_count}. '
                f'Продавец: {seller.username}'
            )
        )

    def _get_seller(self) -> User:
        """Возвращает демо-продавца, создавая его при необходимости."""
        seller, _ = User.objects.get_or_create(
            username='demo_seller',
            defaults={
                'email': 'demo_seller@carhub.local',
                'phone': '+79990000001',
                'role': User.SELLER,
            },
        )
        if not seller.has_usable_password():
            seller.set_password('DemoSeller123!')
            seller.save(update_fields=['password'])
        return seller

    def _get_brand(self, name: str) -> Brand:
        """Возвращает марку автомобиля."""
        brand, _ = Brand.objects.get_or_create(name=name)
        return brand

    def _get_model(self, brand: Brand, name: str) -> Model:
        """Возвращает модель автомобиля внутри конкретной марки."""
        model, _ = Model.objects.get_or_create(brand=brand, name=name)
        return model

    def _attach_image(self, car: Car, image_path: Path, code: str) -> None:
        """Прикрепляет подходящую картинку, не создавая дубликат при повторном запуске."""
        target_name = f'{code}_{image_path.name}'
        if car.main_image and target_name in car.main_image.name:
            return

        with image_path.open('rb') as source:
            car.main_image.save(target_name, File(source), save=False)

    def _seed_data(self) -> list[dict[str, Any]]:
        """Возвращает объявления, где фото соответствует модели автомобиля."""
        return [
            {
                'code': 'rav4-01',
                'brand': 'Toyota',
                'model': 'RAV4',
                'image': 'rav4.jpg',
                'year': 2022,
                'mileage': 42000,
                'price': '3250000.00',
                'views': 18,
                'description': 'Toyota RAV4 в хорошем состоянии, полный привод, аккуратная эксплуатация.',
            },
            {
                'code': 'rav4-02',
                'brand': 'Toyota',
                'model': 'RAV4',
                'image': 'rav4.jpg',
                'year': 2021,
                'mileage': 61000,
                'price': '2890000.00',
                'views': 25,
                'description': 'Toyota RAV4 после одного владельца, обслуживалась по регламенту.',
            },
            {
                'code': 'rav4-03',
                'brand': 'Toyota',
                'model': 'RAV4',
                'image': 'rav4.jpg',
                'year': 2023,
                'mileage': 17000,
                'price': '3680000.00',
                'views': 31,
                'description': 'Свежая Toyota RAV4 с небольшим пробегом и богатой комплектацией.',
            },
            {
                'code': 'sclass-01',
                'brand': 'Mercedes-Benz',
                'model': 'S-Класс',
                'image': 's-class.webp',
                'year': 2020,
                'mileage': 54000,
                'price': '7350000.00',
                'views': 44,
                'description': 'Mercedes-Benz S-Класс, представительский седан с комфортным салоном.',
            },
            {
                'code': 'sclass-02',
                'brand': 'Mercedes-Benz',
                'model': 'S-Класс',
                'image': 's-class.webp',
                'year': 2021,
                'mileage': 39000,
                'price': '8250000.00',
                'views': 52,
                'description': 'Mercedes-Benz S-Класс в отличном состоянии, премиальная комплектация.',
            },
            {
                'code': 'zafira-01',
                'brand': 'Opel',
                'model': 'Zafira',
                'image': 'zafira.webp',
                'year': 2016,
                'mileage': 126000,
                'price': '1180000.00',
                'views': 12,
                'description': 'Opel Zafira, семейный минивэн, просторный салон и экономичный мотор.',
            },
            {
                'code': 'zafira-02',
                'brand': 'Opel',
                'model': 'Zafira',
                'image': 'zafira.webp',
                'year': 2017,
                'mileage': 109000,
                'price': '1320000.00',
                'views': 16,
                'description': 'Opel Zafira с прозрачной историей обслуживания и хорошей комплектацией.',
            },
            {
                'code': 'zafira-03',
                'brand': 'Opel',
                'model': 'Zafira',
                'image': 'zafira.webp',
                'year': 2015,
                'mileage': 148000,
                'price': '990000.00',
                'views': 9,
                'description': 'Opel Zafira для семьи, технически исправна, вложений не требует.',
            },
            {
                'code': 'polo-01',
                'brand': 'Volkswagen',
                'model': 'Polo',
                'image': 'polo.webp',
                'year': 2019,
                'mileage': 83000,
                'price': '1050000.00',
                'views': 27,
                'description': 'Volkswagen Polo, надежный городской седан с небольшим расходом топлива.',
            },
            {
                'code': 'polo-02',
                'brand': 'Volkswagen',
                'model': 'Polo',
                'image': 'polo.webp',
                'year': 2020,
                'mileage': 69000,
                'price': '1190000.00',
                'views': 34,
                'description': 'Volkswagen Polo в ухоженном состоянии, удобен для города и трассы.',
            },
        ]
