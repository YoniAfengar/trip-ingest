"""Load parsed trips into Postgres in batches."""
from __future__ import annotations

from itertools import batched
from typing import Iterable

import psycopg

from trip_ingest.model import Trip


def load_trips(
    conn: psycopg.Connection,
    trips: Iterable[Trip],
    batch_size: int = 1000,
) -> int:
    """Insert trips in batches and return the number actually inserted."""
    inserted_count = 0

    with conn.cursor() as cur:
        for batch in batched(trips, batch_size):
            rows = [
                (
                    trip.trip_id,
                    trip.station_id,
                    trip.started_at,
                    trip.distance_m,
                )
                for trip in batch
            ]

            if not rows:
                continue

            placeholders = ",".join(
                ["(%s, %s, %s, %s)"] * len(rows)
            )

            values: list[object] = []

            for row in rows:
                values.extend(row)

            cur.execute(
                f"""
                INSERT INTO trips (
                    trip_id,
                    station_id,
                    started_at,
                    distance_m
                )
                VALUES {placeholders}
                ON CONFLICT (trip_id) DO NOTHING
                """,
                values,
            )

            inserted_count += cur.rowcount

    return inserted_count