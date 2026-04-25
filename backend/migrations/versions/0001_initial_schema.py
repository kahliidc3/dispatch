"""Initial schema for dispatch.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-04-23
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA_SQL_PATH = Path(__file__).with_name("0001_initial_schema.sql")


def upgrade() -> None:
    bind = op.get_bind()
    bind.exec_driver_sql(
        _SCHEMA_SQL_PATH.read_text(encoding="utf-8"),
        execution_options={"no_parameters": True},
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.exec_driver_sql("DROP SCHEMA IF EXISTS public CASCADE;")
    bind.exec_driver_sql("CREATE SCHEMA public;")
