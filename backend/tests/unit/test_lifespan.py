from types import SimpleNamespace

import pytest
from fastapi import FastAPI

from apps.api import lifespan as lifespan_module


@pytest.mark.asyncio
async def test_app_lifespan_calls_startup_and_shutdown(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    async def fake_init_db() -> None:
        calls.append("init")

    async def fake_dispose_db() -> None:
        calls.append("dispose")

    def fake_configure_logging(*, service_name: str, log_level: str) -> None:
        calls.append(f"log:{service_name}:{log_level}")

    monkeypatch.setattr(
        lifespan_module,
        "get_settings",
        lambda: SimpleNamespace(service_name="dispatch-test", log_level="DEBUG"),
    )
    monkeypatch.setattr(lifespan_module, "init_db", fake_init_db)
    monkeypatch.setattr(lifespan_module, "dispose_db", fake_dispose_db)
    monkeypatch.setattr(lifespan_module, "configure_logging", fake_configure_logging)

    async with lifespan_module.app_lifespan(FastAPI()):
        calls.append("inside")

    assert calls == ["log:dispatch-test:DEBUG", "init", "inside", "dispose"]
