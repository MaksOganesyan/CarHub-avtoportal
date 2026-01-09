from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from ...models import Car


class Command(BaseCommand):
    help = 'Удаляет объявления старше 1 года со статусом sold'

    def handle(self, *args, **options):
        old_date = timezone.now() - timedelta(days=365)
        deleted = Car.objects.filter(status='sold', created_at__lt=old_date).delete()
        self.stdout.write(self.style.SUCCESS(f'Удалено {deleted[0]} старых объявлений'))
