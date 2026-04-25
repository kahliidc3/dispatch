import pytest

from apps.api.deps import get_settings_dep
from libs.core.config import get_settings, reset_settings_cache


def test_get_settings_uses_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:khalid123@postgres:5432/dispatch",
    )
    monkeypatch.setenv("DEFAULT_DOMAIN_HOURLY_RATE_LIMIT", "175")

    reset_settings_cache()
    settings = get_settings()

    assert settings.database_url == "postgresql+asyncpg://postgres:khalid123@postgres:5432/dispatch"
    assert settings.default_domain_hourly_rate_limit == 175

    reset_settings_cache()


def test_get_settings_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERVICE_NAME", "dispatch-test")

    reset_settings_cache()
    first = get_settings()
    second = get_settings()

    assert first is second
    assert first.service_name == "dispatch-test"

    reset_settings_cache()


def test_get_settings_dependency_returns_cached_settings() -> None:
    reset_settings_cache()
    assert get_settings_dep() is get_settings()
    reset_settings_cache()
