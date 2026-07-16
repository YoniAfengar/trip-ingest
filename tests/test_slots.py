"""Task 7 — at most two ingests at a time."""
from __future__ import annotations

import psycopg
import pytest

from trip_ingest import errors
from trip_ingest.slots import job_slot


def _in_use(conn: psycopg.Connection) -> int:
    row = conn.execute("SELECT in_use FROM job_slots WHERE job_name = 'ingest'").fetchone()
    assert row is not None
    return int(row[0])


def test_taking_a_permit_is_visible_to_everyone_else(conn: psycopg.Connection):
    """The whole point of a permit is that *other* processes can see it. If this fails, your
    increment is sitting inside a transaction nobody has committed."""
    assert _in_use(conn) == 0
    with job_slot("ingest"):
        assert _in_use(conn) == 1
    assert _in_use(conn) == 0


def test_two_jobs_may_run_at_once(conn: psycopg.Connection):
    with job_slot("ingest"), job_slot("ingest"):
        assert _in_use(conn) == 2
    assert _in_use(conn) == 0


def test_the_third_job_waits_and_then_gives_up(conn: psycopg.Connection):
    with job_slot("ingest"), job_slot("ingest"):
        with pytest.raises(errors.SlotUnavailable):
            with job_slot("ingest", timeout=0.5):
                pytest.fail("a third job must not get a permit")
    assert _in_use(conn) == 0


def test_a_permit_is_given_back_when_the_job_crashes(conn: psycopg.Connection):
    with pytest.raises(RuntimeError):
        with job_slot("ingest"):
            raise RuntimeError("the drop was corrupt and the job died")
    assert _in_use(conn) == 0, "a crashed job kept its permit forever; nothing will ever run again"
