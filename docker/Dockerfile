FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*
COPY requirements/production.txt /app/requirements/
COPY requirements/base.txt /app/requirements/
RUN pip install --no-cache-dir -r requirements/production.txt
COPY . /app/
RUN mkdir -p /app/logs
RUN python manage.py collectstatic --noinput
COPY docker/entrypoint.sh /app/docker/entrypoint.sh
RUN chmod +x /app/docker/entrypoint.sh
ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "2", "config.wsgi:application"]
