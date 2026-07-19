"""Tasks 2 and 3 — get rows out of a file, and turn them into trips."""
from __future__ import annotations
from trip_ingest import errors
import json
from pathlib import Path
from typing import Iterator
from datetime import datetime
from trip_ingest.model import RawRow, Trip


def read_drop(path: Path) -> Iterator[RawRow]:
    """Yield one raw JSON object per line of a `.jsonl` drop.

    Task 2. A drop is a night's trips: it does not fit in memory, and on a bad night it does not fit
    on the machine. Nothing that reads it may hold more than one line at a time.
    """
    with path.open("r") as f:
        for line in f:
            if line.strip(): 
                yield json.loads(line)


def parse_row(raw: RawRow) -> Trip:
    """Turn one raw JSON object into a `Trip`, or raise. Task 3."""

    try:
        trip_id = raw["trip_id"]
        station_id = raw["station_id"]
        distance_m = raw["distance_m"]
    except KeyError as e:
        raise errors.MissingField from e

    try:
        started_at = datetime.fromisoformat(raw["started_at"])
    except (KeyError, ValueError) as e:
        raise errors.BadTimestamp from e

    if distance_m < 0:
        raise errors.NegativeDistance

    return Trip(
        trip_id=trip_id,
        station_id=station_id,
        started_at=started_at,
        distance_m=distance_m,
    )
