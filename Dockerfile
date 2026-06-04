# Dockerfile для CarHub
# Для разработки: использует runserver (по умолчанию)
# Для продакшена: docker-compose.prod.yml переопределяет command на gunicorn
FROM python:3.13

WORKDIR /app

# Установка зависимостей (включая gunicorn, celery и т.д.)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код проекта
COPY . .

# В продакшене статику собираем при билде (или в CI)
# В compose.prod мы монтируем volume ./staticfiles
RUN python manage.py collectstatic --noinput || true

# Development по умолчанию.
# В production compose мы делаем:
#   command: gunicorn carhub.wsgi:application --bind 0.0.0.0:8000 --workers 4
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
