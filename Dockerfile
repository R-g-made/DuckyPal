# Используем легкий образ Python
FROM python:3.11-slim

# Установка системных зависимостей для сборки некоторых пакетов (например, psycopg2)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Установка зависимостей Python
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Команда для запуска бота
CMD ["python", "main.py"]
