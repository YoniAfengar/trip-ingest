"""Task 6 — wire it together. Task 7 — and then make sure only two of these run at once."""
from __future__ import annotations

from pathlib import Path

import psycopg

from trip_ingest.model import Report


def ingest_drop(conn: psycopg.Connection, path: Path, rejects_dir: Path) -> Report:
    """Read one drop, load the good rows, write the bad ones aside, and report what happened.

    A rejected row must not stop the job, and it must not vanish either: write it to
    `rejects_dir/<drop-name>.rejects.jsonl`, one JSON object per line, each carrying the original row
    and why it was rejected. Somebody will have to fix these in the morning.
    """
    raise NotImplementedError


def run_job(drop_dir: Path, rejects_dir: Path = Path("rejects")) -> Report:
    """Ingest every `*.jsonl` in `drop_dir` and return the totals across all of them.

    Task 6. Log a structured summary — one line, at INFO, naming the counts — so that a person on
    call at 3am can tell what happened without opening the database.

    Task 7. Two of these may run at once. A third must wait.
    """
    raise NotImplementedError
