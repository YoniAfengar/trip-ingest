"""Tasks 2 and 3 — get rows out of a file, and turn them into trips."""
from __future__ import annotations

from pathlib import Path
from typing import Iterator

from trip_ingest.model import RawRow, Trip


def read_drop(path: Path) -> Iterator[RawRow]:
    """Yield one raw JSON object per line of a `.jsonl` drop.

    Task 2. A drop is a night's trips: it does not fit in memory, and on a bad night it does not fit
    on the machine. Nothing that reads it may hold more than one line at a time.
    """
    raise NotImplementedError


def parse_row(raw: RawRow) -> Trip:
    """Turn one raw JSON object into a `Trip`, or raise. Task 3."""
    raise NotImplementedError
