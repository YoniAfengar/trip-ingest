"""Task 3 — name the failures.

One base class is here. The rest is yours, and the shape of the tree is the design decision: a caller
must be able to catch "this row is bad, skip it and keep going" **without** also catching "the job
cannot run at all". If a single `except` can swallow both, the hierarchy is wrong.

`tests/test_errors.py` says exactly which exceptions must exist and how they must relate.
"""
from __future__ import annotations


class IngestError(Exception):
    """Anything this ingest raises on purpose."""

class RowError(IngestError):
    """A single row is bad, skip it and keep going."""
    pass
class MissingField(RowError):
    """A required field is missing."""
    pass
class BadTimestamp(RowError):
    """The timestamp is not a valid ISO 8601 string."""
    pass
class NegativeDistance(RowError):
    """The distance is negative."""
    pass
class JobError(IngestError):
    """The job cannot run at all."""
    pass
class SlotUnavailable(JobError):
    """The job cannot run because the slot is already taken."""
    pass

# TODO Task 3.
