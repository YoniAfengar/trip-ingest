"""Tasks 4 and 7 — the schema, and the fact that it can be undone."""
from __future__ import annotations

import psycopg

from trip_ingest.migrate import downgrade_to_base, upgrade_to_head


def _columns(conn: psycopg.Connection, table: str) -> dict[str, str]:
    rows = conn.execute(
        "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s",
        (table,)).fetchall()
    return {name: dtype for name, dtype in rows}


def test_trips_table_exists(migrated: str):
    with psycopg.connect(migrated) as conn:
        cols = _columns(conn, "trips")
    assert set(cols) >= {"trip_id", "station_id", "started_at", "distance_m"}
    assert cols["started_at"] == "timestamp with time zone", "a naive timestamp is a future outage"


def test_trip_id_is_the_key_the_loader_needs(migrated: str):
    """Task 5 asks the database to ignore a trip it already has. It can only do that if it knows
    what 'already has' means."""
    with psycopg.connect(migrated) as conn:
        keys = conn.execute("""
            SELECT a.attname FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = 'trips'::regclass AND i.indisprimary
        """).fetchall()
    assert [k for (k,) in keys] == ["trip_id"]


def test_job_slots_is_seeded_with_two_permits(migrated: str):
    with psycopg.connect(migrated) as conn:
        row = conn.execute(
            "SELECT capacity, in_use FROM job_slots WHERE job_name = 'ingest'").fetchone()
    assert row is not None, "the 'ingest' row must be created by the migration, not by the app"
    assert row[0] == 2
    assert row[1] == 0


def test_the_chain_runs_backwards_and_forwards(migrated: str):
    """Every revision has a `downgrade()`. A migration you cannot undo is a migration you cannot
    deploy on a Friday. This walks the whole chain to `base` and back to `head`."""
    downgrade_to_base()
    with psycopg.connect(migrated) as conn:
        left = conn.execute(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name IN ('trips', 'job_slots')").fetchone()
    assert left is not None and left[0] == 0, "downgrade left tables behind"
    upgrade_to_head()
