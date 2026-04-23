"""Sprint 03 identity infrastructure deltas.

Revision ID: 0003_sprint03_identity_infrastructure
Revises: 0002_auth_sessions_and_api_key_last4
Create Date: 2026-04-23
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0003_sprint03_identity_infrastructure"
down_revision: str | None = "0002_auth_sessions_and_api_key_last4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "domain_dns_records",
        sa.Column("verification_status", sa.String(length=20), nullable=True),
    )
    op.execute(
        "UPDATE domain_dns_records SET verification_status = 'pending' "
        "WHERE verification_status IS NULL"
    )
    op.alter_column("domain_dns_records", "verification_status", nullable=False)
    op.create_check_constraint(
        "ck_domain_dns_records_verification_status",
        "domain_dns_records",
        "verification_status IN ('pending','verified','failed')",
    )

    op.add_column(
        "ses_configuration_sets",
        sa.Column("event_destination_sns_topic_arn", sa.Text(), nullable=True),
    )

    op.add_column(
        "domains",
        sa.Column("default_configuration_set_id", postgresql.UUID(as_uuid=False), nullable=True),
    )
    op.create_foreign_key(
        "fk_domains_default_configuration_set_id_ses_configuration_sets",
        "domains",
        "ses_configuration_sets",
        ["default_configuration_set_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column(
        "sender_profiles",
        sa.Column("ip_pool_id", postgresql.UUID(as_uuid=False), nullable=True),
    )
    op.create_foreign_key(
        "fk_sender_profiles_ip_pool_id_ip_pools",
        "sender_profiles",
        "ip_pools",
        ["ip_pool_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_sender_profiles_ip_pool_id",
        "sender_profiles",
        ["ip_pool_id"],
        unique=False,
    )

    op.add_column(
        "ip_pools",
        sa.Column(
            "dedicated_ips",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.execute("UPDATE ip_pools SET dedicated_ips = '[]'::jsonb WHERE dedicated_ips IS NULL")
    op.alter_column("ip_pools", "dedicated_ips", nullable=False)


def downgrade() -> None:
    op.drop_column("ip_pools", "dedicated_ips")

    op.drop_index("ix_sender_profiles_ip_pool_id", table_name="sender_profiles")
    op.drop_constraint(
        "fk_sender_profiles_ip_pool_id_ip_pools",
        "sender_profiles",
        type_="foreignkey",
    )
    op.drop_column("sender_profiles", "ip_pool_id")

    op.drop_constraint(
        "fk_domains_default_configuration_set_id_ses_configuration_sets",
        "domains",
        type_="foreignkey",
    )
    op.drop_column("domains", "default_configuration_set_id")

    op.drop_column("ses_configuration_sets", "event_destination_sns_topic_arn")

    op.drop_constraint(
        "ck_domain_dns_records_verification_status",
        "domain_dns_records",
        type_="check",
    )
    op.drop_column("domain_dns_records", "verification_status")
