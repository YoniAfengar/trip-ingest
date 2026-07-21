# 🚆 Trip Ingest Pipeline

![Trip Ingest Pipeline](screenshots/trip-ingest.png)

> **Production-ready ETL pipeline for validating, processing, and loading large JSONL datasets into PostgreSQL using Python, Docker, Alembic, and automated testing.**

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Alembic](https://img.shields.io/badge/Alembic-Database%20Migrations-orange?style=for-the-badge)
![Pytest](https://img.shields.io/badge/Pytest-Tested-success?style=for-the-badge)
![MyPy](https://img.shields.io/badge/MyPy-Type%20Checked-blue?style=for-the-badge)

---

# ✨ Highlights

- 🚀 Stream-based ingestion for large JSONL datasets
- 📦 Batch ETL processing with configurable batch size
- 🔒 Idempotent database loading using PostgreSQL constraints
- ❌ Automatic reject handling for invalid records
- 🐳 Fully Dockerized development environment
- 🗄️ Alembic database migrations
- ✅ Automated testing with Pytest
- 🔍 Static type checking with MyPy
- 🏗️ Production-style project architecture

---

# 📖 Overview

Trip Ingest Pipeline is a production-style ETL project that demonstrates how to ingest large JSONL datasets into PostgreSQL using modern Python engineering practices.

The pipeline validates incoming records, separates invalid data into reject files, performs efficient batch inserts, guarantees idempotent loading, and produces execution summaries.

The project emphasizes clean architecture, automated testing, reproducible environments, and maintainable code rather than simply loading data into a database.

---

# 🏗️ Architecture

```text
             JSONL Drop Files
                    │
                    ▼
           JSON Validation
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
   Valid Records         Invalid Records
        │                       │
        ▼                       ▼
 Batch Processing        Reject File (.jsonl)
        │
        ▼
 PostgreSQL Database
        │
        ▼
 Execution Summary
```

---

# 🛠️ Technology Stack

| Category | Technologies |
|-----------|--------------|
| Language | Python 3.12 |
| Database | PostgreSQL |
| Containerization | Docker & Docker Compose |
| Database Migrations | Alembic |
| Testing | Pytest |
| Type Checking | MyPy |
| Version Control | Git |

---

# 📂 Project Structure

```text
trip-ingest/
├── src/
│   └── trip_ingest/
├── tests/
├── migrations/
├── sample_data/
├── rejects/
├── screenshots/
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── README.md
```

---

# 🚀 Key Features

## Streaming Ingestion

Processes input efficiently without loading the entire dataset into memory.

---

## Data Validation

Each record is validated before reaching the database.

Invalid records are written into reject files without stopping the pipeline.

---

## Batch Loading

Valid records are inserted in configurable batches for improved performance.

---

## Idempotent Processing

Duplicate executions never insert the same record twice.

---

## Production-Oriented Design

- Dockerized environment
- Database migrations
- Automated tests
- Static type checking
- Clean project structure

---

# ⚙️ Quick Start

Clone the repository:

```bash
git clone git@github.com:YoniAfengar/trip-ingest.git
cd trip-ingest
```

Start PostgreSQL:

```bash
docker compose up -d
```

Apply migrations:

```bash
uv run alembic upgrade head
```

Run the pipeline:

```bash
uv run trip-ingest
```

---

# 🧪 Running Tests

Run the complete test suite:

```bash
uv run pytest
```

Run end-to-end tests:

```bash
uv run pytest -m e2e
```

Run type checking:

```bash
uv run mypy src
```

---

# 📈 Engineering Principles

This project focuses on applying software engineering best practices to ETL development.

Key principles include:

- Clean Architecture
- Separation of Concerns
- Reproducible Environments
- Automated Testing
- Type Safety
- Database Migrations
- Maintainable Code
- Production-style Development Workflow

---

# 🚀 Future Improvements

- Apache Airflow orchestration
- Cloud deployment
- Monitoring & logging
- CI/CD pipeline
- Performance benchmarking

---

# 👨‍💻 Author

**Yonatan Afengar**

Senior BI Developer transitioning into modern Data Engineering through production-ready Python projects.

- 💼 LinkedIn: https://www.linkedin.com/in/yonatan-afengar-92bb18155/
- 💻 GitHub: https://github.com/YoniAfengar