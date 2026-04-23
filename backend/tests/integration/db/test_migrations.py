from __future__ import annotations

import os
from uuid import uuid4

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url

from libs.core.config import get_settings, reset_settings_cache


def _to_sync_url(url: str) -> str:
    parsed = make_url(url)
    if parsed.drivername.endswith("+asyncpg"):
        parsed = parsed.set(drivername="postgresql+psycopg")
    return parsed.render_as_string(hide_password=False)


def _pg_database_exists(connection: psycopg.Connection, db_name: str) -> bool:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        return cursor.fetchone() is not None


@pytest.mark.integration
def test_migrations_apply_full_initial_schema() -> None:
    original_database_url = os.getenv("DATABASE_URL")
    base_async_url = os.getenv("DATABASE_URL", get_settings().database_url)
    base_sync_url = _to_sync_url(base_async_url)
    parsed = make_url(base_sync_url)
    admin_sync_url = parsed.set(database="postgres").render_as_string(hide_password=False)

    try:
        admin_conn = psycopg.connect(admin_sync_url, autocommit=True)
    except psycopg.Error as exc:
        pytest.skip(f"Postgres not available for migration integration test: {exc}")

    test_db_name = f"dispatch_mig_{uuid4().hex[:10]}"
    test_async_url = make_url(base_async_url).set(database=test_db_name).render_as_string(
        hide_password=False,
    )
    test_sync_url = make_url(base_sync_url).set(database=test_db_name).render_as_string(
        hide_password=False,
    )

    with admin_conn:
        with admin_conn.cursor() as cursor:
            cursor.execute(f'CREATE DATABASE "{test_db_name}"')

    os.environ["DATABASE_URL"] = test_async_url
    reset_settings_cache()

    try:
        alembic_config = Config("alembic.ini")
        command.upgrade(alembic_config, "head")

        with psycopg.connect(test_sync_url) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_type = 'BASE TABLE'
                    """
                )
                table_count_row = cursor.fetchone()
                assert table_count_row is not None
                table_count = table_count_row[0]
                assert table_count == 39

                cursor.execute("SELECT to_regclass('public.messages')")
                message_row = cursor.fetchone()
                assert message_row is not None
                assert message_row[0] == "messages"

                cursor.execute("SELECT to_regclass('public.suppression_entries')")
                suppression_row = cursor.fetchone()
                assert suppression_row is not None
                assert suppression_row[0] == "suppression_entries"

                cursor.execute("SELECT to_regclass('public.user_sessions')")
                sessions_row = cursor.fetchone()
                assert sessions_row is not None
                assert sessions_row[0] == "user_sessions"

                cursor.execute(
                    """
                    SELECT matviewname
                    FROM pg_matviews
                    WHERE schemaname = 'public' AND matviewname = 'mv_domain_health'
                    """
                )
                view_row = cursor.fetchone()
                assert view_row is not None
                assert view_row[0] == "mv_domain_health"
    finally:
        reset_settings_cache()
        if original_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = original_database_url

        with psycopg.connect(admin_sync_url, autocommit=True) as cleanup_conn:
            with cleanup_conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = %s AND pid <> pg_backend_pid()
                    """,
                    (test_db_name,),
                )
                if _pg_database_exists(cleanup_conn, test_db_name):
                    cursor.execute(f'DROP DATABASE "{test_db_name}"')
