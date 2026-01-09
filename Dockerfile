# Dockerfile
FROM python:3.13

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Собираем статику (для DRF browsable API и наших стилей)
RUN python manage.py collectstatic --noinput

# Запускаем сервер
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
