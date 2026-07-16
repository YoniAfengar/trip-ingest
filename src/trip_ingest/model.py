"""The one row this pipeline moves. Given — do not edit."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, TypeAlias

# One line of a drop, straight from `json.loads`. Nothing has been checked yet — that is `parse_row`'s
# job, and the name is here to say so out loud.
RawRow: TypeAlias = dict[str, Any]


@dataclass(frozen=True, slots=True)
class Trip:
    trip_id: str
    station_id: str
    started_at: datetime
    distance_m: int


@dataclass(frozen=True, slots=True)
class Report:
    """What one drop did. `read` counts lines; `loaded` counts rows the database did not already
    have; `rejected` counts rows that never reached it."""
    read: int
    loaded: int
    rejected: int
