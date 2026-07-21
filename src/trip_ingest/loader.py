"""Load parsed trips into Postgres in batches."""
from __future__ import annotations

from itertools import batched
from typing import Iterable

import psycopg

from trip_ingest.model import Trip


SQL = """
INSERT INTO trips (
    trip_id,
    station_id,
    started_at,
    distance_m
)
VALUES {placeholders}
ON CONFLICT (trip_id) DO NOTHING
"""


def _rows(batch: tuple[Trip, ...]) -> list[tuple[object, object, object, object]]:
    return [
        (
            trip.trip_id,
            trip.station_id,
            trip.started_at,
            trip.distance_m,
        )
        for trip in batch
    ]


def _placeholders(count: int) -> str:
    return ",".join(["(%s, %s, %s, %s)"] * count)


def _values(rows: list[tuple[object, object, object, object]]) -> list[object]:
    values: list[object] = []
    for row in rows:
        values.extend(row)
    return values


def load_trips(
    conn: psycopg.Connection,
    trips: Iterable[Trip],
    batch_size: int = 1000,
) -> int:
    """Insert trips in batches and return the number actually inserted."""
    inserted = 0

    with conn.cursor() as cur:
        for batch in batched(trips, batch_size):
            rows = _rows(batch)
            if not rows:
                continue

            cur.execute(
                SQL.format(placeholders=_placeholders(len(rows))),
                _values(rows),
            )
            inserted += cur.rowcount

    return inserted