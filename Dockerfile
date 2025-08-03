# Dockerfile
FROM python:3.11-slim

# Установка рабочей директории внутри контейнера
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Открываем порт 5000
EXPOSE 5000

# Команда по умолчанию — запуск веб-сервера
CMD ["python", "run.py"]