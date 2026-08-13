#!/bin/sh
set -e

echo "[entrypoint] Waiting for PostgreSQL at ${DATABASE_URL}"
until python -c "import os,sys; import psycopg2; psycopg2.connect(os.environ['DATABASE_URL']).close()" 2>/dev/null; do
  echo "[entrypoint] PostgreSQL unavailable - retrying in 2s"
  sleep 2
done
echo "[entrypoint] PostgreSQL is up"

echo "[entrypoint] Running migrations"
python manage.py migrate --noinput

echo "[entrypoint] Collecting static files"
python manage.py collectstatic --noinput

echo "[entrypoint] Starting gunicorn"
exec gunicorn config.wsgi:application -b 0.0.0.0:8000 --workers 3
