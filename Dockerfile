# Dockerfile
FROM python:3.13

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Собираем статику
RUN python manage.py collectstatic --noinput

# По умолчанию dev, для prod: CMD gunicorn ...
# Для деплоя: docker run ... gunicorn carhub.wsgi:application --bind 0.0.0.0:8000 --workers 4
# Пример prod CMD:
# CMD ["gunicorn", "carhub.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "4"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
