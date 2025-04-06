# Используем базовый образ Python
FROM python:3.9-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем локальные файлы в контейнер
COPY . /app

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    python3-dev

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Запускаем Python скрипт (crawler)
CMD ["bash"]