
"""Task 7 — at most two ingests at a time."""
from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Iterator

import psycopg

from trip_ingest import errors
from trip_ingest.settings import database_url


@contextmanager
def job_slot(job_name: str, timeout: float = 30.0) -> Iterator[None]:
    """Hold one of `job_name`'s permits for the duration of the block.

    Take a permit if one is free. If none is, wait for one — up to `timeout` seconds, then raise.
    Give the permit back when the block ends, however it ends.
    """
    deadline = time.monotonic() + timeout
    acquired = False

    with psycopg.connect(database_url(), autocommit=True) as conn:
        while time.monotonic() < deadline:
            row = conn.execute(
                """
                UPDATE job_slots
                SET in_use = in_use + 1
                WHERE job_name = %s
                  AND in_use < capacity
                RETURNING in_use
                """,
                (job_name,),
            ).fetchone()

            if row is not None:
                acquired = True
                break

            time.sleep(0.1)

        if not acquired:
            raise errors.SlotUnavailable(
                f"No permit available for job '{job_name}'"
            )

        try:
            yield
        finally:
            conn.execute(
                """
                UPDATE job_slots
                SET in_use = in_use - 1
                WHERE job_name = %s
                """,
                (job_name,),
            )