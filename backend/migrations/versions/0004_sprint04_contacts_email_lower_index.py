"""Sprint 04 contact uniqueness hardening.

Revision ID: 0004_contacts_email_idx
Revises: 0003_identity_infra
Create Date: 2026-04-23
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004_contacts_email_idx"
down_revision: str | None = "0003_identity_infra"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ux_contacts_email_lower",
        "contacts",
        [sa.text("lower(email)")],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ux_contacts_email_lower", table_name="contacts")
