"""Task 7 — at most two ingests at a time."""
from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Iterator

import psycopg

from trip_ingest import errors
from trip_ingest.settings import database_url


ACQUIRE_SQL = """
UPDATE job_slots
SET in_use = in_use + 1
WHERE job_name = %s
  AND in_use < capacity
RETURNING in_use
"""

RELEASE_SQL = """
UPDATE job_slots
SET in_use = in_use - 1
WHERE job_name = %s
"""


def _try_acquire(conn: psycopg.Connection, job_name: str) -> bool:
    row = conn.execute(ACQUIRE_SQL, (job_name,)).fetchone()
    return row is not None


def _release(conn: psycopg.Connection, job_name: str) -> None:
    conn.execute(RELEASE_SQL, (job_name,))


def _wait_for_permit(
    conn: psycopg.Connection,
    job_name: str,
    timeout: float,
) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _try_acquire(conn, job_name):
            return
        time.sleep(0.1)
    raise errors.SlotUnavailable(
        f"No permit available for job '{job_name}'"
    )


@contextmanager
def job_slot(job_name: str, timeout: float = 30.0) -> Iterator[None]:
    """Hold one of job_name's permits for the duration of the block."""
    with psycopg.connect(database_url(), autocommit=True) as conn:
        _wait_for_permit(conn, job_name, timeout)
        try:
            yield
        finally:
            _release(conn, job_name)