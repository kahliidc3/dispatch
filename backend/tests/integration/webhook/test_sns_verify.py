from __future__ import annotations

import base64
from datetime import UTC, datetime, timedelta

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.x509.oid import NameOID

from apps.webhook import sns_verify


def _certificate_material() -> tuple[rsa.RSAPrivateKey, bytes]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name(
        [x509.NameAttribute(NameOID.COMMON_NAME, "sns.us-east-1.amazonaws.com")]
    )
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(UTC) - timedelta(days=1))
        .not_valid_after(datetime.now(UTC) + timedelta(days=7))
        .sign(private_key, hashes.SHA256())
    )
    pem = cert.public_bytes(serialization.Encoding.PEM)
    return private_key, pem


def _signed_notification(*, private_key: rsa.RSAPrivateKey) -> dict[str, str]:
    envelope = {
        "Type": "Notification",
        "MessageId": "sns-msg-verify-1",
        "TopicArn": "arn:aws:sns:us-east-1:123456789012:dispatch-events",
        "Message": '{"eventType":"Delivery","mail":{"messageId":"ses-1"}}',
        "Timestamp": "2026-04-24T10:00:00.000Z",
        "SignatureVersion": "2",
        "SigningCertURL": (
            "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-test.pem"
        ),
    }
    canonical = sns_verify._build_canonical_message(envelope)  # noqa: SLF001
    signature = private_key.sign(canonical, padding.PKCS1v15(), hashes.SHA256())
    envelope["Signature"] = base64.b64encode(signature).decode("ascii")
    return envelope


def test_verify_sns_signature_accepts_valid_signature(monkeypatch: pytest.MonkeyPatch) -> None:
    private_key, cert_pem = _certificate_material()
    envelope = _signed_notification(private_key=private_key)

    monkeypatch.setattr(sns_verify, "_load_signing_certificate", lambda *_args, **_kwargs: cert_pem)
    result = sns_verify.verify_sns_signature(envelope)

    assert result.verified is True


def test_verify_sns_signature_rejects_invalid_signature(monkeypatch: pytest.MonkeyPatch) -> None:
    private_key, cert_pem = _certificate_material()
    envelope = _signed_notification(private_key=private_key)
    envelope["Signature"] = base64.b64encode(b"invalid-signature").decode("ascii")

    monkeypatch.setattr(sns_verify, "_load_signing_certificate", lambda *_args, **_kwargs: cert_pem)
    result = sns_verify.verify_sns_signature(envelope)

    assert result.verified is False


def test_validate_signing_cert_url_rejects_non_sns_host() -> None:
    with pytest.raises(sns_verify.SnsVerificationError):
        sns_verify.validate_signing_cert_url("https://evil.example.com/cert.pem")
