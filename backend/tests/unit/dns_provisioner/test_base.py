from __future__ import annotations

import base64

import pytest

from libs.core.config import Settings
from libs.core.errors import ValidationError
from libs.dns_provisioner.base import AwsSecretsManagerSecretProvider, normalize_dns_value


class _FakeSecretsManagerClient:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload
        self.calls = 0

    def get_secret_value(self, **kwargs: object) -> dict[str, object]:
        _ = kwargs
        self.calls += 1
        return dict(self.payload)


@pytest.mark.asyncio
async def test_secret_provider_reads_and_caches_secret_string() -> None:
    settings = Settings(app_env="test")
    client = _FakeSecretsManagerClient({"SecretString": "super-secret"})
    provider = AwsSecretsManagerSecretProvider(settings, client=client)

    first = await provider.get_secret(secret_name="dispatch/cloudflare")
    second = await provider.get_secret(secret_name="dispatch/cloudflare")

    assert first == "super-secret"
    assert second == "super-secret"
    assert client.calls == 1


@pytest.mark.asyncio
async def test_secret_provider_supports_secret_binary_base64() -> None:
    settings = Settings(app_env="test")
    encoded = base64.b64encode(b'{"token":"abc"}').decode("utf-8")
    client = _FakeSecretsManagerClient({"SecretBinary": encoded})
    provider = AwsSecretsManagerSecretProvider(settings, client=client)

    secret = await provider.get_secret(secret_name="dispatch/cloudflare")

    assert secret == '{"token":"abc"}'


@pytest.mark.asyncio
async def test_secret_provider_rejects_empty_secret_name() -> None:
    settings = Settings(app_env="test")
    client = _FakeSecretsManagerClient({"SecretString": "unused"})
    provider = AwsSecretsManagerSecretProvider(settings, client=client)

    with pytest.raises(ValidationError):
        await provider.get_secret(secret_name=" ")


def test_normalize_dns_value_strips_quotes_case_and_dot() -> None:
    assert normalize_dns_value(' "VALUE.Example.COM." ') == "value.example.com"
