from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self) -> None:
        """
        Регистрирует сигналы и периодические задачи при загрузке приложения.

        - PeriodicTask (через post_migrate) для ежедневной очистки старых SOLD-объявлений.
        - social_account_added для автоматической выдачи роли SELLER при OAuth.
        """
        from django.db.models.signals import post_migrate
        from django.dispatch import receiver
        from allauth.socialaccount.signals import social_account_added
        from .models import User

        @receiver(post_migrate)
        def register_cleanup_periodic_task(sender, **kwargs):
            """
            Регистрирует периодическую задачу очистки старых проданных объявлений.
            Срабатывает после миграций django_celery_beat (когда таблицы PeriodicTask готовы).
            """
            if sender.name not in ('django_celery_beat', 'core'):
                return
            try:
                from django_celery_beat.models import PeriodicTask, IntervalSchedule
                schedule, _ = IntervalSchedule.objects.get_or_create(
                    every=1,
                    period=IntervalSchedule.DAYS,
                )
                PeriodicTask.objects.get_or_create(
                    interval=schedule,
                    name='Cleanup old sold cars daily',
                    task='core.tasks.cleanup_old_sold_cars',
                    defaults={'description': 'Ежедневная очистка проданных объявлений старше 1 года'},
                )
            except Exception:
                # Таблицы ещё не созданы во время ранних стадий migrate
                pass

        @receiver(social_account_added)
        def set_seller_role_on_social_signup(sender, request, sociallogin, **kwargs):
            """После успешного OAuth (Google/VK) принудительно ставим роль SELLER (бизнес-правило)."""
            user = sociallogin.user
            if user.role != User.SELLER:
                user.role = User.SELLER
                user.save()
