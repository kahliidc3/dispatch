import pytest

from apps.scheduler import beat
from apps.workers.celery_app import celery_app


def test_celery_app_configuration() -> None:
    assert celery_app.conf.task_acks_late is True
    assert celery_app.conf.task_reject_on_worker_lost is True
    assert celery_app.conf.worker_prefetch_multiplier == 1


def test_scheduler_beat_main_invokes_celery_start(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[list[str]] = []

    def fake_start(*, argv: list[str]) -> None:
        captured.append(argv)

    monkeypatch.setattr(celery_app, "start", fake_start)
    beat.main()

    assert captured == [["celery", "beat", "-l", "info"]]
