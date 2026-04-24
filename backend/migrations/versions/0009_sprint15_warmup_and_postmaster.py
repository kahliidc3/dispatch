"""Add warmup columns to domains; create postmaster_metrics table.

Revision ID: 0009_warmup_postmaster
Revises: 0008_domain_provisioning_status
Create Date: 2026-04-24
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009_warmup_postmaster"
down_revision: str | None = "0008_domain_provisioning_status"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "domains",
        sa.Column(
            "warmup_stage",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'none'"),
        ),
    )
    op.alter_column("domains", "warmup_stage", server_default=None)

    op.add_column(
        "domains",
        sa.Column(
            "warmup_schedule",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
    )
    op.alter_column("domains", "warmup_schedule", server_default=None)

    op.create_table(
        "postmaster_metrics",
        sa.Column("id", sa.Uuid(as_uuid=False), primary_key=True),
        sa.Column(
            "domain_id",
            sa.Uuid(as_uuid=False),
            sa.ForeignKey("domains.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("domain_reputation", sa.String(20), nullable=True),
        sa.Column("spam_rate", sa.Numeric(10, 6), nullable=True),
        sa.Column("dkim_success_ratio", sa.Numeric(6, 4), nullable=True),
        sa.Column("spf_success_ratio", sa.Numeric(6, 4), nullable=True),
        sa.Column("dmarc_success_ratio", sa.Numeric(6, 4), nullable=True),
        sa.Column("inbound_encryption_ratio", sa.Numeric(6, 4), nullable=True),
        sa.Column("raw_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_postmaster_metrics_domain_id", "postmaster_metrics", ["domain_id"])
    op.create_unique_constraint(
        "uq_postmaster_metrics_domain_date",
        "postmaster_metrics",
        ["domain_id", "date"],
    )


def downgrade() -> None:
    op.drop_table("postmaster_metrics")
    op.drop_column("domains", "warmup_schedule")
    op.drop_column("domains", "warmup_stage")
