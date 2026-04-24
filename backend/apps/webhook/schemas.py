from __future__ import annotations

import json
from datetime import datetime

from pydantic import BaseModel, Field


class SnsEnvelope(BaseModel):
    type: str = Field(alias="Type")
    message_id: str = Field(alias="MessageId")
    topic_arn: str = Field(alias="TopicArn")
    message: str = Field(alias="Message")
    timestamp: datetime = Field(alias="Timestamp")
    signature_version: str = Field(alias="SignatureVersion")
    signature: str = Field(alias="Signature")
    signing_cert_url: str = Field(alias="SigningCertURL")
    subject: str | None = Field(default=None, alias="Subject")
    unsubscribe_url: str | None = Field(default=None, alias="UnsubscribeURL")
    subscribe_url: str | None = Field(default=None, alias="SubscribeURL")
    token: str | None = Field(default=None, alias="Token")

    @property
    def is_notification(self) -> bool:
        return self.type == "Notification"

    @property
    def is_subscription_confirmation(self) -> bool:
        return self.type == "SubscriptionConfirmation"

    def to_sns_dict(self) -> dict[str, str]:
        payload = {
            "Type": self.type,
            "MessageId": self.message_id,
            "TopicArn": self.topic_arn,
            "Message": self.message,
            "Timestamp": self.timestamp.isoformat().replace("+00:00", "Z"),
            "SignatureVersion": self.signature_version,
            "Signature": self.signature,
            "SigningCertURL": self.signing_cert_url,
        }
        if self.subject is not None:
            payload["Subject"] = self.subject
        if self.unsubscribe_url is not None:
            payload["UnsubscribeURL"] = self.unsubscribe_url
        if self.subscribe_url is not None:
            payload["SubscribeURL"] = self.subscribe_url
        if self.token is not None:
            payload["Token"] = self.token
        return payload

    def parse_message_json(self) -> dict[str, object]:
        try:
            raw = json.loads(self.message)
        except json.JSONDecodeError as exc:
            raise ValueError("SNS message payload must be valid JSON") from exc

        if not isinstance(raw, dict):
            raise ValueError("SNS message payload must be an object")
        return raw
