# Подготовка CarHub к деплою на сервер (пункт 3 на отлично)

## Основная идея

В проде используем:
- Gunicorn вместо runserver
- Тот же SQLite (как и в разработке)
- Redis + Celery worker + Celery Beat
- Реальный SMTP (не Mailhog)
- Переменные окружения через `.env.prod`

Всё запускается через Docker.

## 1. .env.prod

Создай файл `.env.prod` (не коммить!):

```env
DEBUG=0
SECRET_KEY=сгенерируй_длинный_случайный_ключ
ALLOWED_HOSTS=localhost,127.0.0.1,твойдомен.ру,www.твойдомен.ру
# Для локального тестирования прод-стека на Windows/Mac добавь localhost выше. На реальном сервере оставь только домены.

CELERY_BROKER_URL=redis://redis:6379/0

EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=1
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...
DEFAULT_FROM_EMAIL=CarHub <noreply@твойдомен.ру>
```

Генерация ключа:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 2. Dockerfile и docker-compose.prod.yml

- В `Dockerfile` уже есть сборка статики.
- В продакшене команда переопределяется на gunicorn.

`docker-compose.prod.yml` поднимает:
- web (gunicorn)
- redis
- celery (worker)
- celery-beat

SQLite в проде сохраняется через volume (`db.sqlite3`).

Запуск:
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

## 3. Основные команды после запуска

```bash
# Миграции
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Создать админа
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Собрать статику
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Логи Celery
docker-compose -f docker-compose.prod.yml logs -f celery
docker-compose -f docker-compose.prod.yml logs -f celery-beat
```

## 4. Celery и Email

- Celery worker и beat работают отдельными сервисами (уже настроено).
- Для писем в проде используй настоящий SMTP в `.env.prod` (Mailgun, Яндекс, Gmail и т.д.).

### Демонстрация Celery на защите (5 доменных задач + периодическая)

Есть специальная команда для быстрого показа **всех** Celery-задач:

```powershell
# 1. Подними инфраструктуру (гибрид: bare runserver + docker worker)
docker-compose up -d redis mailhog celery celery-beat

# 2. (опционально, но рекомендуется) наполни красивыми данными с фото
python manage.py seed_cars

# 3. В одном терминале следи за worker'ом
docker-compose logs -f celery

# 4. В другом терминале запускай демонстрацию
python manage.py demo_celery
```

Команда `demo_celery` (core/management/commands/demo_celery.py) ставит в реальную очередь:
- send_welcome_email
- send_car_submitted_for_moderation
- process_car_image (с PIL)
- send_car_approved_notification
- cleanup_old_sold_cars

Письма прилетят в Mailhog (http://localhost:8025).

Для чисто прод-стека:
```powershell
docker-compose -f docker-compose.prod.yml up -d --build
docker-compose -f docker-compose.prod.yml exec web python manage.py demo_celery
docker-compose -f docker-compose.prod.yml logs -f celery
```

Дополнительно на защите покажи:
- В /admin/ раздел "Periodic tasks" — "Cleanup old sold cars daily" (зарегистрирована в core/apps.py через post_migrate).
- `python manage.py clean_old_cars` (management command-компаньон).
- В коде: все `.delay()` вызовы (views.py, api.py, serializers.py) + 5 функций в core/tasks.py.

## 5. Статика и медиа

- `collectstatic` выполняется при сборке образа.
- Медиа и статика сохраняются через volumes в compose.
- При необходимости можно добавить nginx для отдачи статики.

## 6. Полезные команды

```bash
# Логи веб-приложения
docker-compose -f docker-compose.prod.yml logs -f web

# Зайти внутрь контейнера
docker-compose -f docker-compose.prod.yml exec web bash

# Остановить всё
docker-compose -f docker-compose.prod.yml down

# Пересобрать один сервис
docker-compose -f docker-compose.prod.yml build web
```

## 7. Минимальные требования безопасности

- `DEBUG=0`
- `SECRET_KEY` вынесен в `.env.prod`
- `ALLOWED_HOSTS` заполнен реальными доменами
- На проде используй HTTPS (Let's Encrypt + nginx при необходимости)
- `.env.prod` не в репозитории

## 8. Отслеживание ошибок — GlitchTip (cloud)

Вместо локального Sentry используем **облачную версию GlitchTip** (чтобы не нагружать систему).

GlitchTip полностью совместим с `sentry-sdk`.

**Как подключить:**

1. Зарегистрируйся на https://glitchtip.com/ (бесплатный план есть).
2. Создай проект → скопируй DSN (пример: `https://<key>@glitchtip.com/<project>/`).
3. Добавь в `.env.prod` (и при желании в dev `.env`):
   ```env
   GLITCHTIP_DSN=https://<key>@glitchtip.com/<project>/
   ```
4. В `settings.py` инициализация происходит автоматически, если DSN задан (и не в тестах).

Это покрывает требование "хорошо" (интеграция системы отслеживания ошибок).

В проде ошибки будут приходить в твой аккаунт GlitchTip с полным трейсом, окружением, версией и т.д.

## 9. Демонстрация GlitchTip на защите (важно для оценки)

Чтобы на защите надёжно показать, что ошибки и 404 реально улетают в облачный GlitchTip:

1. Убедись, что `.env.prod` содержит правильный `GLITCHTIP_DSN` (без кавычек вокруг URL!).
2. Пересобери и подними прод-стек:
   ```powershell
   docker-compose -f docker-compose.prod.yml build web
   docker-compose -f docker-compose.prod.yml up -d --force-recreate
   ```
3. Выполни миграции (если нужно):
   ```powershell
   docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
   ```
4. Для демонстрации **404**:
   - Открой в браузере `http://localhost:8000/несуществующая-страница-xyz123/`
   - Должен показаться простой 404 (из `templates/404.html`).
   - Через 5-30 сек ошибка появится в дашборде GlitchTip (Issues) как "error" уровень.
5. Для **гарантированной ошибки** (самый надёжный способ показать на защите):
   - Открой `http://localhost:8000/trigger-glitchtip-error/`
   - Страница упадёт с 500 (ZeroDivisionError).
   - Ошибка **точно** появится в GlitchTip (DjangoIntegration ловит исключения + явный capture_exception + capture_message).
6. Проверь в дашборде https://app.glitchtip.com/ — там должны быть:
   - Сообщения о 404
   - Исключение ZeroDivisionError с трейсом
   - Ваше кастомное сообщение "GlitchTip demo..."
7. Посмотреть логи контейнера (на случай вопросов) — ищи строку STARTUP:
   ```powershell
   docker-compose -f docker-compose.prod.yml logs --tail 30 web | Select-String -Pattern "STARTUP|GlitchTip|ERROR|Exception"
   ```
   В выводе должно быть примерно:
   >>> STARTUP: DEBUG=False, DJANGO_ENV=production, GLITCHTIP_DSN=set

8. Диагностика внутри контейнера (если вдруг всё ещё DEBUG=True):
   ```powershell
   docker-compose -f docker-compose.prod.yml exec web python -c "
   import os, django
   os.environ.setdefault('DJANGO_SETTINGS_MODULE','carhub.settings')
   django.setup()
   from django.conf import settings
   print('Effective DEBUG:', settings.DEBUG)
   print('DJANGO_ENV:', os.environ.get('DJANGO_ENV'))
   "
   ```

После демонстрации (по желанию) можно убрать/закомментировать путь trigger-glitchtip-error в `carhub/urls.py`, но для защиты он полезен.

**Важно:** всегда запускай прод именно так:
`docker-compose -f docker-compose.prod.yml build web`
`docker-compose -f docker-compose.prod.yml up -d --force-recreate`
(Обычный `docker-compose up` поднимает dev-стек с DEBUG=1 и живым монтированием кода — поэтому ты видишь отладочную страницу Django.)

В settings.py есть принудительная логика: при DJANGO_ENV=production DEBUG всегда становится False.

Это "другой" надёжный подход: вместо надежды только на автоматический лог 404 мы добавили явный триггер исключения + принудительный capture в handler404.


