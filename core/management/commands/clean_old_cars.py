from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from ...models import Car


class Command(BaseCommand):
    """
    Management command для ручного запуска очистки старых проданных объявлений.

    Используется вместе с периодической Celery-задачей cleanup_old_sold_cars.
    """
    help = 'Удаляет объявления автомобилей со статусом SOLD старше 365 дней'

    def handle(self, *args, **options) -> None:
        """Выполняет удаление старых SOLD-объявлений."""
        cutoff = timezone.now() - timedelta(days=365)
        qs = Car.objects.filter(status=Car.SOLD, created_at__lt=cutoff)
        count = qs.count()
        if count > 0:
            qs.delete()
            self.stdout.write(self.style.SUCCESS(f'Удалено {count} старых проданных объявлений'))
        else:
            self.stdout.write(self.style.WARNING('Старых проданных объявлений для удаления нет'))
