# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:0.9.10-python3.11-trixie-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv

# Create app directory in container
WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-editable

COPY project/ /app/project/

WORKDIR /app/project

RUN chmod +x /app/project/runserver.sh

EXPOSE 8000

CMD [ "./runserver.sh" ]