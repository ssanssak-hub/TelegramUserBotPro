# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# نصب وابستگی‌های سیستم
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# کپی فایل‌های پروژه
COPY requirements-complete.txt .
RUN pip install --no-cache-dir -r requirements-complete.txt

COPY . .

# ایجاد پوشه‌های لازم
RUN mkdir -p data downloads logs sessions backups

# ایجاد کاربر غیر root
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# محیط اجرا
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# اجرای ربات
CMD ["python", "main.py"]
