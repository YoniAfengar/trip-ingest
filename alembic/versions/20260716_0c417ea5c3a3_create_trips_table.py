"""create trips table

Revision ID: 0c417ea5c3a3
Revises: 
Create Date: 2026-07-16 14:35:13.107360
"""
from __future__ import annotations

from alembic import op

revision = '0c417ea5c3a3'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE TABLE trips(trip_id INTEGER PRIMARY KEY, station_id INTEGER, started_at TIMESTAMPTZ, distance_m integer)")


def downgrade() -> None:
    op.execute("DROP TABLE trips")
