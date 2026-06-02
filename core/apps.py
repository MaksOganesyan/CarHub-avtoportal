from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        from django.db.models.signals import post_migrate
        from django.dispatch import receiver

        @receiver(post_migrate)
        def register_periodic_tasks(sender, **kwargs):
            if sender.name != 'django_celery_beat':
                return
            # Автоматическая регистрация периодической задачи для Celery Beat (пункт 1 на отлично)
            from django_celery_beat.models import PeriodicTask, IntervalSchedule
            try:
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
                pass

        # Для OAUTH2 (allauth social signup) - принудительно роль SELLER
        from allauth.socialaccount.signals import social_account_added
        from .models import User

        @receiver(social_account_added)
        def set_seller_role_on_social_signup(sender, request, sociallogin, **kwargs):
            user = sociallogin.user
            if user.role != User.SELLER:
                user.role = User.SELLER
                user.save()
