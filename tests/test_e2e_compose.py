"""Task 8 — your Dockerfile, your compose file, a real database. Given — do not edit.

    uv run pytest -m e2e

This is skipped by default (see `addopts` in `pyproject.toml`) because it builds images from scratch
and takes minutes. It is skipped by a **marker**, which is a statement of intent — not by an
environment variable, which would be a statement of nothing.

What it does, in order: builds with `--no-cache`, brings up `db`, drops fresh files into `drops/`,
runs `ingest` as a one-off container, and then looks in Postgres from *outside* the compose network
to see whether the rows arrived. Then it runs the ingest a second time and checks that nothing moved.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Iterator

import psycopg
import pytest

from trip_ingest.settings import DEFAULT_DSN

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.e2e


def _compose(*args: str, timeout: int = 600) -> subprocess.CompletedProcess:
    proc = subprocess.run(["docker", "compose", *args], cwd=ROOT, capture_output=True,
                          text=True, timeout=timeout)
    if proc.returncode != 0:
        pytest.fail(f"`docker compose {' '.join(args)}` failed:\n{proc.stdout}\n{proc.stderr}",
                    pytrace=False)
    return proc


def _wait_for_postgres(deadline: float = 60.0) -> None:
    """Poll the DSN from the host. This is also the test of your published port."""
    end = time.monotonic() + deadline
    while time.monotonic() < end:
        try:
            with psycopg.connect(DEFAULT_DSN, connect_timeout=2):
                return
        except psycopg.OperationalError:
            time.sleep(1)
    pytest.fail(f"Postgres never became reachable at {DEFAULT_DSN}", pytrace=False)


def _good(n: int) -> str:
    return json.dumps({"trip_id": f"E2E-{n}", "station_id": "ST-99",
                       "started_at": f"2026-03-14T0{n}:00:00+00:00", "distance_m": 1000})


def _write_drops() -> None:
    """Two fresh drops: four good rows in total, and two rows that must never reach the table."""
    drops, rejects = ROOT / "drops", ROOT / "rejects"
    for directory in (drops, rejects):
        shutil.rmtree(directory, ignore_errors=True)
        directory.mkdir(parents=True)
    (drops / "e2e-clean.jsonl").write_text(f"{_good(1)}\n{_good(2)}\n")
    (drops / "e2e-dirty.jsonl").write_text("\n".join([
        _good(3),
        json.dumps({"station_id": "ST-99"}),                                    # no trip_id
        _good(4),
        json.dumps({"trip_id": "E2E-BAD", "station_id": "ST-99",                # unusable timestamp
                    "started_at": "never", "distance_m": 5}),
    ]) + "\n")


def _trip_count() -> int:
    with psycopg.connect(DEFAULT_DSN) as conn:
        row = conn.execute("SELECT count(*) FROM trips WHERE trip_id LIKE 'E2E-%'").fetchone()
    assert row is not None
    return int(row[0])


@pytest.fixture(scope="module")
def stack() -> Iterator[None]:
    _compose("build", "--no-cache")
    _compose("up", "-d", "db")
    _wait_for_postgres()
    yield
    _compose("down", "-v", timeout=120)


def test_the_ingest_container_reaches_the_database_container(stack: None):
    _write_drops()
    _compose("run", "--rm", "ingest")

    assert _trip_count() == 4, "the good rows did not arrive"
    rejects = list((ROOT / "rejects").glob("*.jsonl"))
    assert rejects, "the two bad rows vanished without a trace"
    bad = [json.loads(line) for f in rejects for line in f.read_text().splitlines()]
    assert len(bad) == 2


def test_running_it_again_changes_nothing(stack: None):
    """Somebody will rerun last night's job. Twice."""
    before = _trip_count()
    _compose("run", "--rm", "ingest")
    assert _trip_count() == before


def test_the_permit_was_given_back(stack: None):
    """Two ingests have now run to completion. If either kept its permit, the next one queues
    forever."""
    with psycopg.connect(DEFAULT_DSN) as conn:
        row = conn.execute("SELECT in_use FROM job_slots WHERE job_name = 'ingest'").fetchone()
    assert row is not None and row[0] == 0
