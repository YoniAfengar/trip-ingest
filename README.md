# Trip Ingestion Pipeline

A production-style data ingestion pipeline built with Python, PostgreSQL, and Docker.

## Overview

This project ingests bike trip data from JSONL files into PostgreSQL.

The pipeline validates incoming records, writes invalid rows to reject files, loads valid trips in batches, prevents duplicate inserts, applies database migrations automatically, and limits concurrent executions using a database-backed permit system.

The application and database run in separate Docker containers and communicate through a Docker Compose network.

## Features

- JSONL trip ingestion
- Record validation and error handling
- Reject files with the original row and failure reason
- Batch loading into PostgreSQL
- Idempotent inserts using `ON CONFLICT`
- Alembic database migrations
- Database-backed concurrency control
- Docker and Docker Compose deployment
- Unit and end-to-end tests
- Static type checking with mypy

## Tech Stack

- Python
- PostgreSQL
- SQL
- Docker
- Docker Compose
- Alembic
- Psycopg
- Pytest
- Mypy
- uv

## Architecture

```text
JSONL drop files
        |
        v
Record parsing and validation
        |
   +----+----+
   |         |
   v         v
Valid rows   Rejected rows
   |         |
   v         v
Batch load   Reject JSONL files
   |
   v
PostgreSQL
```

## Reliability Features

### Idempotency

The `trips` table uses `trip_id` as a primary key. Inserts use PostgreSQL `ON CONFLICT DO NOTHING`, so running the same ingest more than once does not create duplicate records.

### Reject Handling

Invalid rows do not stop the entire job. Each rejected row is written to a separate JSONL file together with the error message, allowing the record to be investigated and corrected later.

### Concurrency Control

A database-backed permit table limits the number of ingest jobs running at the same time. Permits are returned in a `finally` block so completed or failed jobs do not permanently consume capacity.

### Database Readiness

The ingest container waits for PostgreSQL to pass its health check before starting. This prevents the application from attempting to connect before the database is ready.

## Docker Networking

The host machine connects to PostgreSQL through:

```text
localhost:55432
```

The ingest container connects through the Docker Compose network using:

```text
db:5432
```

Inside a container, `localhost` refers to that container itself. The Compose service name `db` is therefore used to reach the PostgreSQL container.

## Running the Project

Install the dependencies:

```bash
uv sync
```

Run the regular test suite:

```bash
uv run pytest
```

Run static type checking:

```bash
uv run mypy src/
```

Run the end-to-end container test from a clean environment:

```bash
docker compose down -v
uv run pytest -m e2e
```

## End-to-End Test

The end-to-end test:

1. Builds the ingest image without cache.
2. Starts PostgreSQL.
3. Waits until the database is healthy.
4. Creates fresh JSONL drop files.
5. Runs the ingest container.
6. Confirms valid rows arrived in PostgreSQL.
7. Confirms invalid rows were written to reject files.
8. Runs the ingest a second time.
9. Confirms no duplicate rows were inserted.
10. Confirms the concurrency permit was returned.

## Project Structure

```text
.
├── alembic/
├── src/trip_ingest/
├── tests/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── alembic.ini
└── ANSWERS.md
```

## What I Learned

This project strengthened my practical understanding of:

- Reliable ETL and data-ingestion design
- PostgreSQL batch loading
- Idempotent processing
- Database migrations
- Error recovery and rejected-record handling
- Docker networking
- Concurrency control
- Test-driven development
- End-to-end testing
- Static type checking