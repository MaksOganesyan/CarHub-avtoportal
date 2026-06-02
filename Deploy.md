# Подготовка проекта CarHub к деплою на сервер (пункт 3 на отлично)

## Основные шаги

1. **Production settings**
   - Создайте `carhub/settings_prod.py` или используйте env vars.
   - DEBUG = False
   - SECRET_KEY из env (не в коде!)
   - ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
   - DATABASES — лучше PostgreSQL (добавьте в compose)
   - STATIC_ROOT, collectstatic
   - Используйте Whitenoise или nginx для статики.

2. **Docker для продакшена**
   - Dockerfile: CMD gunicorn carhub.wsgi:application -b 0.0.0.0:8000 --workers 4 --threads 4
   - docker-compose.prod.yml с:
     - web (gunicorn)
     - db (postgres)
     - redis
     - celery
     - nginx (опционально)

3. **Зависимости**
   - requirements.txt имеет gunicorn.
   - Для prod: pip install -r requirements.txt

4. **База данных**
   - В dev sqlite, в prod:
     - docker run postgres
     - Или в compose.

5. **Переменные окружения**
   Используйте .env:
   ```
   DEBUG=0
   SECRET_KEY=your-super-secret
   ALLOWED_HOSTS=yourdomain.com
   DATABASE_URL=...
   SENTRY_DSN=...
   CELERY_BROKER_URL=redis://redis:6379/0
   ```

6. **Статические файлы и медиа**
   - collectstatic при билде.
   - Медиа через volume или S3.

7. **Celery и Mail в прод**
   - Используйте реальный SMTP (не mailhog).
   - Celery worker + beat на сервере.

8. **Безопасность**
   - HTTPS (Let's Encrypt)
   - Firewall
   - Обновления

## Пример запуска на VPS

```bash
# На сервере
git clone ...
cd ...
docker-compose -f docker-compose.prod.yml up -d
```

Документируйте в отчёте: использовали Docker для изолированного деплоя, gunicorn для WSGI, Celery для фоновых задач.

Обновите Dockerfile и docker-compose как в текущей версии проекта.