"""Bring the database to the newest revision, from Python. Given — do not edit.

Production applies migrations the same way the tests do and the same way the container does: by
running the revisions you wrote. There is no second description of the schema anywhere.
"""
from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

ROOT = Path(__file__).resolve().parents[2]


def _config() -> Config:
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    return cfg


def upgrade_to_head() -> None:
    command.upgrade(_config(), "head")


def downgrade_to_base() -> None:
    command.downgrade(_config(), "base")
