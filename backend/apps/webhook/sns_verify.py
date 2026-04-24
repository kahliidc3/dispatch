from __future__ import annotations

import base64
import time
from dataclasses import dataclass
from urllib.parse import urlparse
from urllib.request import urlopen

from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

from libs.core.config import Settings, get_settings

_CANONICAL_FIELDS: dict[str, list[str]] = {
    "Notification": ["Message", "MessageId", "Subject", "Timestamp", "TopicArn", "Type"],
    "SubscriptionConfirmation": [
        "Message",
        "MessageId",
        "SubscribeURL",
        "Timestamp",
        "Token",
        "TopicArn",
        "Type",
    ],
    "UnsubscribeConfirmation": [
        "Message",
        "MessageId",
        "SubscribeURL",
        "Timestamp",
        "Token",
        "TopicArn",
        "Type",
    ],
}

_VALID_HOST_SUFFIXES = (".amazonaws.com", ".amazonaws.com.cn")
_CERT_CACHE: dict[str, tuple[bytes, float]] = {}


class SnsVerificationError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class SnsVerificationResult:
    verified: bool
    reason: str | None = None


def validate_signing_cert_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme.lower() != "https":
        raise SnsVerificationError("SigningCertURL must use https")

    if parsed.port not in (None, 443):
        raise SnsVerificationError("SigningCertURL must use port 443")

    host = (parsed.hostname or "").lower()
    if not host.startswith("sns."):
        raise SnsVerificationError("SigningCertURL host must start with sns.")
    if not host.endswith(_VALID_HOST_SUFFIXES):
        raise SnsVerificationError("SigningCertURL host must be an AWS SNS domain")

    if not parsed.path.lower().endswith(".pem"):
        raise SnsVerificationError("SigningCertURL must point to a .pem certificate")

    return url


def _build_canonical_message(envelope: dict[str, str]) -> bytes:
    sns_type = envelope.get("Type")
    if sns_type not in _CANONICAL_FIELDS:
        raise SnsVerificationError(f"Unsupported SNS Type: {sns_type}")

    lines: list[str] = []
    for key in _CANONICAL_FIELDS[sns_type]:
        value = envelope.get(key)
        if value is None:
            if key == "Subject":
                continue
            raise SnsVerificationError(f"Missing SNS field for signature: {key}")

        lines.append(key)
        lines.append(str(value))

    canonical = "\n".join(lines) + "\n"
    return canonical.encode("utf-8")


def _load_signing_certificate(url: str, settings: Settings) -> bytes:
    now = time.time()
    cached = _CERT_CACHE.get(url)
    if cached is not None and cached[1] > now:
        return cached[0]

    with urlopen(url, timeout=2.0) as response:  # noqa: S310
        pem_bytes = response.read()

    _CERT_CACHE[url] = (pem_bytes, now + settings.sns_signature_cert_cache_ttl_seconds)
    return pem_bytes


def verify_sns_signature(
    envelope: dict[str, str],
    *,
    settings: Settings | None = None,
) -> SnsVerificationResult:
    current_settings = settings or get_settings()

    try:
        cert_url = validate_signing_cert_url(envelope["SigningCertURL"])
        canonical = _build_canonical_message(envelope)

        signature_b64 = envelope.get("Signature", "")
        signature = base64.b64decode(signature_b64)

        cert_pem = _load_signing_certificate(cert_url, current_settings)
        cert = x509.load_pem_x509_certificate(cert_pem)
        public_key = cert.public_key()

        version = envelope.get("SignatureVersion")
        if version == "1":
            algorithm: hashes.HashAlgorithm = hashes.SHA1()
        elif version == "2":
            algorithm = hashes.SHA256()
        else:
            raise SnsVerificationError(f"Unsupported SignatureVersion: {version}")

        public_key.verify(signature, canonical, padding.PKCS1v15(), algorithm)
        return SnsVerificationResult(verified=True)
    except (InvalidSignature, KeyError, ValueError, SnsVerificationError):
        return SnsVerificationResult(verified=False, reason="signature_verification_failed")


def confirm_sns_subscription(*, subscribe_url: str) -> bool:
    parsed = urlparse(subscribe_url)
    if parsed.scheme.lower() != "https":
        return False

    host = (parsed.hostname or "").lower()
    if not host.startswith("sns."):
        return False
    if not host.endswith(_VALID_HOST_SUFFIXES):
        return False

    if parsed.port not in (None, 443):
        return False

    with urlopen(subscribe_url, timeout=2.0) as response:  # noqa: S310
        return response.status in {200, 201, 202, 204}


def clear_cert_cache() -> None:
    _CERT_CACHE.clear()
