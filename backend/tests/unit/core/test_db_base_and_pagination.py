from datetime import UTC, datetime

from libs.core.db.base import NAMING_CONVENTION, metadata
from libs.core.db.pagination import decode_cursor, encode_cursor


def test_metadata_uses_naming_convention() -> None:
    assert metadata.naming_convention == NAMING_CONVENTION


def test_cursor_encode_decode_roundtrip() -> None:
    now = datetime.now(UTC)
    encoded = encode_cursor(now, "abc-123")
    decoded_dt, decoded_id = decode_cursor(encoded)

    assert decoded_id == "abc-123"
    assert decoded_dt.isoformat() == now.isoformat()
