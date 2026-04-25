"""Add paused message status transition support for circuit breakers.

Revision ID: 0007_message_paused_status
Revises: 0006_domain_rate_limit
Create Date: 2026-04-24
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007_message_paused_status"
down_revision: str | None = "0006_domain_rate_limit"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE messages DROP CONSTRAINT IF EXISTS messages_status_check;")
    op.execute(
        """
        ALTER TABLE messages
        ADD CONSTRAINT messages_status_check
        CHECK (
            status IN (
                'queued','paused','sending','sent','delivered','bounced','complained','failed','skipped'
            )
        );
        """
    )
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

            IF (OLD.status = 'queued' AND NEW.status = 'paused')
                OR (OLD.status = 'queued' AND NEW.status = 'sending')
                OR (OLD.status = 'paused' AND NEW.status IN ('queued','failed'))
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


def downgrade() -> None:
    op.execute("ALTER TABLE messages DROP CONSTRAINT IF EXISTS messages_status_check;")
    op.execute(
        """
        ALTER TABLE messages
        ADD CONSTRAINT messages_status_check
        CHECK (
            status IN (
                'queued','sending','sent','delivered','bounced','complained','failed','skipped'
            )
        );
        """
    )
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
