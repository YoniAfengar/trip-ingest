"""Task 6 — wire it together. Task 7 — allow only two ingests at once."""
from __future__ import annotations

import json
import logging
from pathlib import Path

import psycopg

from trip_ingest.loader import load_trips
from trip_ingest.model import Report, Trip
from trip_ingest.reader import parse_row
from trip_ingest.settings import database_url
from trip_ingest.slots import job_slot


def _write_reject(
    reject_path: Path,
    line: str,
    error: Exception,
) -> None:
    rejected_row = {"row": line, "error": str(error)}
    with reject_path.open("a") as reject_file:
        reject_file.write(json.dumps(rejected_row) + "\n")


def _read_drop(
    path: Path,
    rejects_dir: Path,
) -> tuple[list[Trip], int, int]:
    trips: list[Trip] = []
    read = 0
    rejected = 0
    rejects_dir.mkdir(parents=True, exist_ok=True)
    reject_path = rejects_dir / f"{path.name}.rejects.jsonl"

    with path.open("r") as file:
        for line in file:
            read += 1
            try:
                trips.append(parse_row(json.loads(line)))
            except Exception as error:
                rejected += 1
                _write_reject(reject_path, line, error)

    return trips, read, rejected


def ingest_drop(
    conn: psycopg.Connection,
    path: Path,
    rejects_dir: Path,
) -> Report:
    """Read one drop, load good rows and write rejected rows aside."""
    trips, read, rejected = _read_drop(path, rejects_dir)
    loaded = load_trips(conn, trips)
    return Report(read=read, loaded=loaded, rejected=rejected)


def _ingest_drops(
    conn: psycopg.Connection,
    drop_dir: Path,
    rejects_dir: Path,
) -> tuple[int, Report]:
    total_drops = 0
    total_read = 0
    total_loaded = 0
    total_rejected = 0

    for drop_path in drop_dir.glob("*.jsonl"):
        total_drops += 1
        report = ingest_drop(conn, drop_path, rejects_dir)
        total_read += report.read
        total_loaded += report.loaded
        total_rejected += report.rejected

    report = Report(
        read=total_read,
        loaded=total_loaded,
        rejected=total_rejected,
    )
    return total_drops, report


def run_job(
    drop_dir: Path,
    rejects_dir: Path = Path("rejects"),
) -> Report:
    """Ingest every JSONL drop and return the combined report."""
    with job_slot("ingest"):
        with psycopg.connect(database_url()) as conn:
            total_drops, report = _ingest_drops(
                conn,
                drop_dir,
                rejects_dir,
            )

        logging.info(
            "Ingest complete: drops=%d read=%d loaded=%d rejected=%d",
            total_drops,
            report.read,
            report.loaded,
            report.rejected,
        )
        return report