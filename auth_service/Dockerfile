# Dockerfile для auth-service
FROM python:3.9-slim

# Установка зависимостей
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходников
COPY . /app/

# Запуск сервера
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]