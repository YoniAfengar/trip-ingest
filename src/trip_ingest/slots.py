"""Task 7 — at most two ingests at a time."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator


@contextmanager
def job_slot(job_name: str, timeout: float = 30.0) -> Iterator[None]:
    """Hold one of `job_name`'s permits for the duration of the block.

    Take a permit if one is free. If none is, wait for one — up to `timeout` seconds, then raise.
    Give the permit back when the block ends, however it ends.

    Read the README before you write this. Two details decide whether it works.
    """
    raise NotImplementedError
    yield   # unreachable; keeps the type of this function a context manager
