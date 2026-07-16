"""Task 3 — name the failures.

One base class is here. The rest is yours, and the shape of the tree is the design decision: a caller
must be able to catch "this row is bad, skip it and keep going" **without** also catching "the job
cannot run at all". If a single `except` can swallow both, the hierarchy is wrong.

`tests/test_errors.py` says exactly which exceptions must exist and how they must relate.
"""
from __future__ import annotations


class IngestError(Exception):
    """Anything this ingest raises on purpose."""


# TODO Task 3.
