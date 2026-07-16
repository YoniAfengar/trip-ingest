"""Task 2 — reading a drop, one line at a time. No database needed."""
from __future__ import annotations

import json
from pathlib import Path

from trip_ingest.reader import read_drop

GOOD = {"trip_id": "T-1", "station_id": "ST-01", "started_at": "2026-03-14T09:15:00+00:00",
        "distance_m": 2400}


def _drop(tmp_path: Path, *lines: str) -> Path:
    path = tmp_path / "2026-03-14.jsonl"
    path.write_text("\n".join(lines) + "\n")
    return path


def test_read_drop_yields_each_row(tmp_path: Path):
    path = _drop(tmp_path, json.dumps(GOOD), json.dumps(GOOD | {"trip_id": "T-2"}))
    assert [row["trip_id"] for row in read_drop(path)] == ["T-1", "T-2"]


def test_read_drop_ignores_a_trailing_blank_line(tmp_path: Path):
    path = _drop(tmp_path, json.dumps(GOOD), "")
    assert len(list(read_drop(path))) == 1


def test_read_drop_does_not_read_the_whole_file(tmp_path: Path):
    """Line 3 is not JSON at all. Taking the first two rows must not touch it — which is only true
    if nothing read ahead. A drop does not fit in memory."""
    path = _drop(tmp_path, json.dumps(GOOD), json.dumps(GOOD | {"trip_id": "T-2"}),
                 "{ this is not json")
    rows = read_drop(path)
    assert next(rows)["trip_id"] == "T-1"
    assert next(rows)["trip_id"] == "T-2"
