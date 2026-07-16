"""Task 5 — put the trips in the database."""
from __future__ import annotations

from typing import Iterable

import psycopg

from trip_ingest.model import Trip


def load_trips(conn: psycopg.Connection, trips: Iterable[Trip], batch_size: int = 1_000) -> int:
    """Insert `trips`, returning how many rows the database did not already have.

    `trips` is an iterable and may be a generator over a file larger than memory — consume it once,
    in batches, and do not build a list of the whole thing.

    Re-running last night's drop must insert nothing and return 0. The database already knows which
    trips it has; ask it, rather than reading it all back to check.
    """
    raise NotImplementedError
