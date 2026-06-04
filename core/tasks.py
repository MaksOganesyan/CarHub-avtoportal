from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging

from .models import Car, User

logger = logging.getLogger(__name__)


@shared_task
def send_car_submitted_for_moderation(car_id: int):
    """
    Асинхронная задача: отправка уведомления модераторам о новом объявлении на модерацию.
    """
    try:
        car = Car.objects.select_related('user', 'brand', 'model').get(id=car_id)
        subject = f'Новое объявление на модерацию: {car.brand} {car.model}'
        message = (
            f'Пользователь {car.user} подал объявление на модерацию.\n\n'
            f'Автомобиль: {car.brand} {car.model} ({car.year})\n'
            f'Цена: {car.price}\n'
            f'Описание: {car.description[:200]}...\n\n'
            f'Проверьте в админке.'
        )
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.DEFAULT_FROM_EMAIL],  # или список модераторов
            fail_silently=False,
        )
        logger.info(f"Sent moderation notification for car {car_id}")
    except Car.DoesNotExist:
        logger.error(f"Car {car_id} not found for moderation notification")
    except Exception as e:
        logger.error(f"Error sending moderation email for car {car_id}: {e}")


@shared_task
def send_car_approved_notification(car_id: int):
    """
    Асинхронная задача: уведомление продавца об одобрении объявления.
    """
    try:
        car = Car.objects.select_related('user', 'brand', 'model').get(id=car_id)
        subject = f'Ваше объявление одобрено: {car.brand} {car.model}'
        message = (
            f'Здравствуйте, {car.user.get_full_name() or car.user.username}!\n\n'
            f'Ваше объявление "{car.brand} {car.model} ({car.year})" было одобрено и опубликовано.\n\n'
            f'Ссылка: http://localhost:8000/car/{car.id}/\n\n'
            f'Удачных продаж!'
        )
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [car.user.email],
            fail_silently=False,
        )
        logger.info(f"Sent approval notification for car {car_id}")
    except Car.DoesNotExist:
        logger.error(f"Car {car_id} not found for approval notification")
    except Exception as e:
        logger.error(f"Error sending approval email for car {car_id}: {e}")


@shared_task
def cleanup_old_sold_cars():
    """
    Периодическая задача: удаление старых проданных объявлений (старше 1 года).
    Обёртка над management command.
    """
    from django.core.management import call_command
    try:
        call_command('clean_old_cars')
        logger.info("Periodic cleanup of old sold cars completed successfully")
    except Exception as e:
        logger.error(f"Error in periodic cleanup: {e}")


@shared_task
def process_car_image(car_id: int):
    """
    Асинхронная обработка изображения автомобиля (ресайз, оптимизация).
    Используется при загрузке фото.
    """
    from PIL import Image
    import os
    try:
        car = Car.objects.get(id=car_id)
        if car.main_image:
            img_path = car.main_image.path
            with Image.open(img_path) as img:
                max_size = 1200
                if max(img.size) > max_size:
                    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                    img.save(img_path, optimize=True, quality=85)
            logger.info(f"Processed image for car {car_id}")
    except Exception as e:
        logger.error(f"Error processing image for car {car_id}: {e}")


@shared_task
def send_welcome_email(user_id: int):
    """
    Асинхронная отправка приветственного письма после регистрации.
    """
    try:
        user = User.objects.get(id=user_id)
        subject = 'Добро пожаловать в CarHub!'
        message = (
            f'Здравствуйте, {user.get_full_name() or user.username}!\n\n'
            f'Спасибо за регистрацию в CarHub — автомобильном портале.\n'
            f'Теперь вы можете размещать объявления о продаже автомобилей (роль Продавец).\n\n'
            f'С уважением,\nКоманда CarHub'
        )
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        logger.info(f"Sent welcome email to user {user_id}")
    except Exception as e:
        logger.error(f"Error sending welcome email to {user_id}: {e}")