"""The entry point. Given — do not edit.

`python -m trip_ingest <drop-dir>` migrates, then runs the job. This is what your `ingest` service
runs in Task 8, and it is why the container must be able to reach the database *before* it loads a
single row.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

from trip_ingest.errors import IngestError
from trip_ingest.ingest import run_job
from trip_ingest.migrate import upgrade_to_head


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    drop_dir = Path(argv[1]) if len(argv) > 1 else Path("drops")
    try:
        upgrade_to_head()
        # Rejects land beside the drops: `drops/` -> `rejects/` on your machine, `/data/drops` ->
        # `/data/rejects` in the container. One rule, both worlds.
        run_job(drop_dir, drop_dir.parent / "rejects")
    except IngestError as exc:
        logging.getLogger("trip_ingest").error("job failed: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
