"""Task 5 — the load. Runs against the Postgres you stood up in Task 1."""
from __future__ import annotations

from datetime import datetime, timezone

import psycopg

from trip_ingest.loader import load_trips
from trip_ingest.model import Trip


def _trip(n: int) -> Trip:
    return Trip(trip_id=f"T-{n}", station_id="ST-01",
                started_at=datetime(2026, 3, 14, 9, 0, tzinfo=timezone.utc), distance_m=100 * n)


def _count(conn: psycopg.Connection) -> int:
    row = conn.execute("SELECT count(*) FROM trips").fetchone()
    assert row is not None
    return int(row[0])


def test_loads_new_trips(clean_trips: psycopg.Connection):
    assert load_trips(clean_trips, [_trip(1), _trip(2)]) == 2
    assert _count(clean_trips) == 2


def test_reloading_the_same_drop_changes_nothing(clean_trips: psycopg.Connection):
    """The nightly job reruns after a failure. It must be safe to rerun."""
    load_trips(clean_trips, [_trip(1), _trip(2)])
    assert load_trips(clean_trips, [_trip(1), _trip(2)]) == 0
    assert _count(clean_trips) == 2


def test_a_partly_overlapping_drop_loads_only_what_is_new(clean_trips: psycopg.Connection):
    load_trips(clean_trips, [_trip(1), _trip(2)])
    assert load_trips(clean_trips, [_trip(2), _trip(3)]) == 1
    assert _count(clean_trips) == 3


def test_accepts_a_generator_and_consumes_it_once(clean_trips: psycopg.Connection):
    """`load_trips` is handed a lazy stream over a file bigger than memory. It may not index it,
    len() it, or walk it twice."""
    assert load_trips(clean_trips, (_trip(n) for n in range(1, 5))) == 4
    assert _count(clean_trips) == 4


def test_loads_more_than_one_batch(clean_trips: psycopg.Connection):
    assert load_trips(clean_trips, (_trip(n) for n in range(1, 251)), batch_size=100) == 250
    assert _count(clean_trips) == 250


def test_an_empty_drop_is_not_an_error(clean_trips: psycopg.Connection):
    assert load_trips(clean_trips, iter(())) == 0
