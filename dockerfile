# Dockerfile
FROM python:3.12-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements.txt и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальной код
COPY . .

# Создаем папки
RUN mkdir -p /app/media /app/staticfiles

# Создаем не-root пользователя
RUN useradd -m -u 1000 django && \
    echo "django ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/django && \
    chmod 0440 /etc/sudoers.d/django && \
    chown -R django:django /app

USER django

# Настраиваем переменные окружения
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=pereval_project.settings

# Порт, который будет слушать приложение
EXPOSE 8000

# Команда для запуска приложения
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]