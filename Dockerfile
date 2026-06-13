FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=2.3.2 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

WORKDIR /app

RUN pip install "poetry==${POETRY_VERSION}"

# Install dependencies first for better layer caching.
COPY pyproject.toml poetry.lock README.md ./
RUN poetry install --only main --no-root

# App code + bundled CSV (so /load/revenues/demo works out of the box).
COPY box_office ./box_office
COPY revenues_per_day.csv ./revenues_per_day.csv

EXPOSE 8000
CMD ["uvicorn", "box_office.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
