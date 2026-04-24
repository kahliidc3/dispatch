"""Enforce one-way message status transitions.

Revision ID: 0005_msg_status_guard
Revises: 0004_contacts_email_idx
Create Date: 2026-04-24
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005_msg_status_guard"
down_revision: str | None = "0004_contacts_email_idx"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION messages_status_transition_guard()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            IF NEW.status = OLD.status THEN
                RETURN NEW;
            END IF;

            IF (OLD.status = 'queued' AND NEW.status = 'sending')
                OR (OLD.status = 'sending' AND NEW.status IN ('sent','failed'))
                OR (OLD.status = 'sent' AND NEW.status IN ('delivered','bounced','complained'))
            THEN
                RETURN NEW;
            END IF;

            RAISE EXCEPTION 'invalid message status transition: % -> %', OLD.status, NEW.status;
        END;
        $$;
        """
    )
    op.execute("DROP TRIGGER IF EXISTS trg_messages_status_transition_guard ON messages;")
    op.execute(
        """
        CREATE TRIGGER trg_messages_status_transition_guard
        BEFORE UPDATE OF status ON messages
        FOR EACH ROW
        EXECUTE FUNCTION messages_status_transition_guard();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_messages_status_transition_guard ON messages;")
    op.execute("DROP FUNCTION IF EXISTS messages_status_transition_guard();")
