from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from libs.core.config import Settings
from libs.dns_provisioner.base import DNSRecordInput
from libs.dns_provisioner.cloudflare import CloudflareDNSProvisioner


class _FakeSecretProvider:
    async def get_secret(self, *, secret_name: str) -> str:
        _ = secret_name
        return '{"api_token":"cf-token"}'


@dataclass(slots=True)
class _FakeCloudflareTransport:
    zones: list[dict[str, str]] = field(
        default_factory=lambda: [{"id": "zone-1", "name": "dispatch.test"}]
    )
    records: dict[str, dict[str, dict[str, str]]] = field(default_factory=dict)
    counter: int = 0

    async def request_json(
        self,
        *,
        method: str,
        path: str,
        token: str,
        params: dict[str, str] | None = None,
        payload: dict[str, object] | None = None,
    ) -> dict[str, object]:
        assert token == "cf-token"
        params = params or {}
        payload = payload or {}
        parts = [part for part in path.split("/") if part]

        if method == "GET" and parts == ["zones"]:
            return {"success": True, "result": list(self.zones), "errors": []}

        if len(parts) >= 3 and parts[0] == "zones" and parts[2] == "dns_records":
            zone_id = parts[1]
            zone_records = self.records.setdefault(zone_id, {})

            if method == "GET":
                requested_name = str(params.get("name", "")).lower().rstrip(".")
                requested_type = str(params.get("type", "")).upper()
                result: list[dict[str, str]] = []
                for record in zone_records.values():
                    if record["name"].lower().rstrip(".") == requested_name and record[
                        "type"
                    ].upper() == requested_type:
                        result.append(dict(record))
                return {"success": True, "result": result, "errors": []}

            if method == "POST":
                self.counter += 1
                record_id = f"rec-{self.counter}"
                zone_records[record_id] = {
                    "id": record_id,
                    "type": str(payload["type"]),
                    "name": str(payload["name"]),
                    "content": str(payload["content"]),
                }
                return {"success": True, "result": dict(zone_records[record_id]), "errors": []}

            if method == "PUT" and len(parts) == 4:
                record_id = parts[3]
                existing = zone_records[record_id]
                existing.update(
                    {
                        "type": str(payload["type"]),
                        "name": str(payload["name"]),
                        "content": str(payload["content"]),
                    }
                )
                return {"success": True, "result": dict(existing), "errors": []}

            if method == "DELETE" and len(parts) == 4:
                record_id = parts[3]
                zone_records.pop(record_id, None)
                return {"success": True, "result": {}, "errors": []}

        raise AssertionError(f"Unhandled Cloudflare fake request: {method} {path}")


@pytest.mark.asyncio
async def test_cloudflare_provisioner_happy_path_upsert_and_verify() -> None:
    settings = Settings(
        app_env="test",
        cloudflare_api_token_secret_name="dispatch/cloudflare/token",
    )
    transport = _FakeCloudflareTransport()
    provisioner = CloudflareDNSProvisioner(
        settings,
        secret_provider=_FakeSecretProvider(),
        transport=transport,
    )

    zones = await provisioner.list_zones()
    assert len(zones) == 1
    assert zones[0].id == "zone-1"

    first_record = DNSRecordInput(
        record_type="TXT",
        name="mail.dispatch.test",
        value="v=spf1 include:amazonses.com -all",
    )
    record_id = await provisioner.create_record(zone_id="zone-1", record=first_record)
    assert record_id.startswith("rec-")

    # Idempotent create should return same record id.
    second_id = await provisioner.create_record(zone_id="zone-1", record=first_record)
    assert second_id == record_id

    # Upsert change should keep id but update content.
    updated_record = DNSRecordInput(
        record_type="TXT",
        name="mail.dispatch.test",
        value="v=spf1 include:amazonses.com ~all",
    )
    third_id = await provisioner.create_record(zone_id="zone-1", record=updated_record)
    assert third_id == record_id

    assert await provisioner.verify_record(zone_id="zone-1", record=updated_record) is True
    assert await provisioner.verify_record(zone_id="zone-1", record=first_record) is False

    await provisioner.delete_record(zone_id="zone-1", record_id=record_id)
    assert await provisioner.verify_record(zone_id="zone-1", record=updated_record) is False
