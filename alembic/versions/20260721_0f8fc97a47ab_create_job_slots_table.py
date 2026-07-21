"""create job slots table

Revision ID: 0f8fc97a47ab
Revises: 0c417ea5c3a3
Create Date: 2026-07-21 14:33:31.602037
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0f8fc97a47ab"
down_revision = "0c417ea5c3a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "job_slots",
        sa.Column(
            "job_name",
            sa.String(),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "capacity",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "in_use",
            sa.Integer(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "capacity > 0",
            name="ck_job_slots_capacity_positive",
        ),
        sa.CheckConstraint(
            "in_use >= 0",
            name="ck_job_slots_in_use_non_negative",
        ),
        sa.CheckConstraint(
            "in_use <= capacity",
            name="ck_job_slots_in_use_capacity",
        ),
    )

    op.execute(
        """
        INSERT INTO job_slots (job_name, capacity, in_use)
        VALUES ('ingest', 2, 0)
        """
    )


def downgrade() -> None:
    op.drop_table("job_slots")