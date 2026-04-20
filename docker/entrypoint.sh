#!/bin/sh
set -e
echo "Waiting for database..."
while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
  sleep 0.1
done
echo "Database is ready!"
echo "Running migrations..."
python manage.py migrate --noinput
echo "Creating logs directory..."
mkdir -p /app/logs
exec "$@"
