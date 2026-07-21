FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini .

RUN pip install --no-cache-dir "psycopg[binary]>=3.2" "alembic>=1.13"

ENV PYTHONPATH=/app/src

CMD ["python", "-m", "trip_ingest", "/data/drops"]