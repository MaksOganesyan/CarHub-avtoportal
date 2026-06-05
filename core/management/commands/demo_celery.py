from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Car, User
from core.tasks import (
    send_welcome_email,
    send_car_submitted_for_moderation,
    send_car_approved_notification,
    process_car_image,
    cleanup_old_sold_cars,
)


class Command(BaseCommand):
    """
    Management command для быстрой демонстрации всех Celery-задач проекта CarHub.

    Запускает .delay() для 5 доменных задач (уведомления, обработка фото, очистка).
    Используется на защите курсовой для показа реальной асинхронности.

    Перед запуском желательно:
      python manage.py seed_cars   (чтобы были красивые авто с фото)
      docker-compose up -d redis mailhog celery celery-beat

    Затем:
      python manage.py demo_celery
    и в соседнем терминале:
      docker-compose logs -f celery
    """

    help = 'Запускает примеры всех Celery-задач (для демонстрации асинхронности на защите)'

    def _safe_delay(self, task_func, *args, label: str = "") -> bool:
        """Безопасно ставит задачу в очередь. Возвращает True при успехе."""
        try:
            task_func.delay(*args)
            return True
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"   [!] Не удалось поставить в очередь {label}: {type(exc).__name__}"))
            self.stdout.write(self.style.WARNING("       Убедись, что запущены: docker-compose up -d redis celery celery-beat"))
            return False

    def handle(self, *args, **options) -> None:
        """Выполняет постановку в очередь примеров всех 5 задач."""
        self.stdout.write(self.style.MIGRATE_HEADING("=== Демонстрация Celery-задач CarHub ==="))
        self.stdout.write("Задачи будут поставлены в очередь Redis и обработаны celery worker'ом.")
        self.stdout.write("Смотри логи: docker-compose logs -f celery (или docker logs ...celery-1)")
        self.stdout.write("Письма: http://localhost:8025\n")

        UserModel = get_user_model()
        queued_count = 0

        # 1. Welcome email (берём или создаём демо-пользователя)
        welcome_user, _ = UserModel.objects.get_or_create(
            username='celery_demo_welcome',
            defaults={
                'email': 'celery_demo@carhub.local',
                'phone': '+79990009999',
                'role': User.SELLER,
            }
        )
        if not welcome_user.has_usable_password():
            welcome_user.set_password('DemoCelery123!')
            welcome_user.save(update_fields=['password'])

        self.stdout.write("1. send_welcome_email (после регистрации)")
        if self._safe_delay(send_welcome_email, welcome_user.id, label="welcome_email"):
            self.stdout.write(self.style.SUCCESS(f"   → queued для user_id={welcome_user.id}"))
            queued_count += 1

        # 2 + 3. Submitted (на модерацию) + обработка изображения
        # Ищем авто с реальной картинкой (лучше после seed_cars)
        car_with_image = Car.objects.filter(main_image__isnull=False).order_by('-id').first()

        if car_with_image:
            self.stdout.write("2. send_car_submitted_for_moderation (новое объявление)")
            if self._safe_delay(send_car_submitted_for_moderation, car_with_image.id, label="submitted"):
                self.stdout.write(self.style.SUCCESS(f"   → queued для car_id={car_with_image.id}"))
                queued_count += 1

            self.stdout.write("3. process_car_image (PIL ресайз + оптимизация)")
            if self._safe_delay(process_car_image, car_with_image.id, label="process_image"):
                self.stdout.write(self.style.SUCCESS(f"   → queued для car_id={car_with_image.id} (с main_image)"))
                queued_count += 1
        else:
            self.stdout.write(self.style.WARNING("   Нет авто с main_image. Запусти сначала: python manage.py seed_cars"))

        # 4. Approved notification (как будто модератор одобрил)
        # Берём любое авто (желательно активное)
        any_car = Car.objects.order_by('-id').first()
        if any_car:
            self.stdout.write("4. send_car_approved_notification (одобрение объявления)")
            if self._safe_delay(send_car_approved_notification, any_car.id, label="approved"):
                self.stdout.write(self.style.SUCCESS(f"   → queued для car_id={any_car.id}"))
                queued_count += 1
        else:
            self.stdout.write(self.style.WARNING("   Нет ни одного объявления в БД."))

        # 5. Периодическая очистка старых проданных
        self.stdout.write("5. cleanup_old_sold_cars (ежедневная периодическая задача)")
        if self._safe_delay(cleanup_old_sold_cars, label="cleanup"):
            self.stdout.write(self.style.SUCCESS("   → queued (периодическая очистка SOLD старше 365 дней)"))
            queued_count += 1

        self.stdout.write("\n" + self.style.SUCCESS(f"=== Готово. Успешно поставлено задач: {queued_count}/5 ==="))
        self.stdout.write("Открой Mailhog http://localhost:8025 чтобы увидеть отправленные письма.")
        self.stdout.write("В логах celery должны появиться строки 'Sent ...', 'Processed image...', 'Periodic cleanup...'.")
        self.stdout.write("Для periodic beat: убедись, что celery-beat запущен и в /admin/ есть 'Cleanup old sold cars daily'.")

        # Дополнительно покажем зарегистрированную periodic задачу
        try:
            from django_celery_beat.models import PeriodicTask
            pt = PeriodicTask.objects.filter(task='core.tasks.cleanup_old_sold_cars').first()
            if pt:
                self.stdout.write(f"\nЗарегистрированная periodic: {pt.name} (interval: {pt.interval}) — enabled={pt.enabled}")
        except Exception:
            pass
