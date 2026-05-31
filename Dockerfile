# Указываем базовый образ
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_CONFIG_VIRTUALENVS_CREATE=false \
    POETRY_HTTP_TIMEOUT=300

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Устанавливаем зависимости системы
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc-dev \
    libpq-dev \
    netcat-openbsd \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Poetry
RUN pip install --default-timeout=100 poetry && \
    poetry config virtualenvs.create false

# Копируем файл с зависимостями и устанавливаем их
COPY pyproject.toml poetry.lock* ./

# Устанавливаем зависимости с помощью Poetry
RUN poetry install --no-root --no-interaction --no-ansi

# Копируем остальные файлы проекта в контейнер
COPY . .

# Открываем порт 8000 для взаимодействия с приложением
EXPOSE 8000
