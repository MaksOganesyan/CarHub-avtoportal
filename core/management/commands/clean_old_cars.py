from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from ...models import Car


class Command(BaseCommand):
    """Команда управления для очистки старых проданных автомобилей (используется в задании)."""
    help = 'Удаляет объявления старше 1 года со статусом sold'

    def handle(self, *args, **options) -> None:
        """Выполняет очистку."""
        old_date = timezone.now() - timedelta(days=365)
        deleted = Car.objects.filter(status=Car.SOLD, created_at__lt=old_date).delete()
        self.stdout.write(self.style.SUCCESS(f'Удалено {deleted[0]} старых объявлений'))
