import json

import pytest

from libs.core.logging import (
    bind_request_context,
    clear_request_context,
    configure_logging,
    get_logger,
    get_request_id,
)


def test_structured_logger_outputs_required_fields(caplog: pytest.LogCaptureFixture) -> None:
    configure_logging(service_name="dispatch-test", log_level="INFO")
    bind_request_context(request_id="req-1", trace_id="trace-1")
    caplog.set_level("INFO")

    logger = get_logger("unit.test")
    logger.info("infra.log.test", foo="bar")

    clear_request_context()

    payload = json.loads(caplog.records[-1].message)

    assert payload["event"] == "infra.log.test"
    assert payload["service"] == "dispatch-test"
    assert payload["request_id"] == "req-1"
    assert payload["trace_id"] == "trace-1"
    assert payload["foo"] == "bar"


def test_clear_request_context_resets_request_id() -> None:
    bind_request_context(request_id="req-2")
    clear_request_context()
    assert get_request_id() is None


def test_logger_redacts_sensitive_values(caplog: pytest.LogCaptureFixture) -> None:
    configure_logging(service_name="dispatch-test", log_level="INFO")
    caplog.set_level("INFO")

    logger = get_logger("unit.test")
    logger.info(
        "infra.log.redaction",
        api_key="ak_live_prefix_secret",
        authorization="Bearer secret-token-value",
        note="token ak_live_deadbeef_deadbeef should be hidden",
    )

    payload = json.loads(caplog.records[-1].message)
    assert payload["api_key"] == "[REDACTED]"
    assert payload["authorization"] == "[REDACTED]"
    assert "ak_live_deadbeef_deadbeef" not in payload["note"]
