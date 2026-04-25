"""Add provisioning_failed domain verification status.

Revision ID: 0008_domain_provisioning_status
Revises: 0007_message_paused_status
Create Date: 2026-04-24
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008_domain_provisioning_status"
down_revision: str | None = "0007_message_paused_status"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE domains DROP CONSTRAINT IF EXISTS domains_verification_status_check;")
    op.execute(
        """
        ALTER TABLE domains
        ADD CONSTRAINT domains_verification_status_check
        CHECK (
            verification_status IN ('pending','verified','failed','disabled','provisioning_failed')
        );
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE domains DROP CONSTRAINT IF EXISTS domains_verification_status_check;")
    op.execute(
        """
        ALTER TABLE domains
        ADD CONSTRAINT domains_verification_status_check
        CHECK (
            verification_status IN ('pending','verified','failed','disabled')
        );
        """
    )
