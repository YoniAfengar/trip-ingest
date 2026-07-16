"""Task 3 — one raw row in, one `Trip` out, or a named failure. No database needed."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from trip_ingest import errors
from trip_ingest.reader import parse_row

GOOD = {"trip_id": "T-1", "station_id": "ST-01", "started_at": "2026-03-14T09:15:00+00:00",
        "distance_m": 2400}


def test_parse_row_builds_a_trip():
    trip = parse_row(GOOD)
    assert trip.trip_id == "T-1"
    assert trip.station_id == "ST-01"
    assert trip.distance_m == 2400
    assert trip.started_at == datetime(2026, 3, 14, 9, 15, tzinfo=timezone.utc)


@pytest.mark.parametrize("field", ["trip_id", "station_id", "distance_m"])
def test_parse_row_rejects_a_missing_field(field: str):
    with pytest.raises(errors.MissingField):
        parse_row({k: v for k, v in GOOD.items() if k != field})


@pytest.mark.parametrize("started_at", ["", "yesterday", "2026-13-45T99:99:99"])
def test_parse_row_rejects_an_unusable_timestamp(started_at: str):
    with pytest.raises(errors.BadTimestamp):
        parse_row(GOOD | {"started_at": started_at})


def test_parse_row_rejects_an_absent_timestamp():
    """A missing `started_at` is a bad timestamp, not a missing field. The row is unusable either
    way; the reject file has to say which, and only one of these is a schema drift."""
    with pytest.raises(errors.BadTimestamp):
        parse_row({k: v for k, v in GOOD.items() if k != "started_at"})


def test_parse_row_rejects_a_negative_distance():
    with pytest.raises(errors.NegativeDistance):
        parse_row(GOOD | {"distance_m": -1})
