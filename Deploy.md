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
ALLOWED_HOSTS=твойдомен.ру,www.твойдомен.ру

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

---


