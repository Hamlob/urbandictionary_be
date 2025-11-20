#!/bin/bash
set -m

T="${RESPONSE_TIMEOUT:-30}"

uv run python manage.py migrate

uv run python manage.py collectstatic --noinput

exec uv run gunicorn project.wsgi:application --keep-alive $T --timeout $T --graceful-timeout $T --bind 0.0.0.0:8000
