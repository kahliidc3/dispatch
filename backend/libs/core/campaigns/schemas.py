from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from libs.core.campaigns.models import Campaign, CampaignRun, Message


class CampaignResponse(BaseModel):
    id: str
    name: str
    status: str
    campaign_type: str
    sender_profile_id: str
    template_version_id: str
    segment_id: str | None
    list_id: str | None
    send_rate_per_hour: int
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, campaign: Campaign) -> CampaignResponse:
        return cls(
            id=campaign.id,
            name=campaign.name,
            status=campaign.status,
            campaign_type=campaign.campaign_type,
            sender_profile_id=campaign.sender_profile_id,
            template_version_id=campaign.template_version_id,
            segment_id=campaign.segment_id,
            list_id=campaign.list_id,
            send_rate_per_hour=campaign.send_rate_per_hour,
            started_at=campaign.started_at,
            completed_at=campaign.completed_at,
            created_at=campaign.created_at,
            updated_at=campaign.updated_at,
        )


class CampaignLaunchResponse(BaseModel):
    campaign: CampaignResponse
    campaign_run_id: str
    run_number: int
    snapshot_rows: int
    created_messages: int
    enqueued_messages: int
    already_launched: bool

    @classmethod
    def build(
        cls,
        *,
        campaign: Campaign,
        campaign_run: CampaignRun,
        snapshot_rows: int,
        created_messages: int,
        enqueued_messages: int,
        already_launched: bool,
    ) -> CampaignLaunchResponse:
        return cls(
            campaign=CampaignResponse.from_model(campaign),
            campaign_run_id=campaign_run.id,
            run_number=campaign_run.run_number,
            snapshot_rows=snapshot_rows,
            created_messages=created_messages,
            enqueued_messages=enqueued_messages,
            already_launched=already_launched,
        )


class CampaignStateChangeResponse(BaseModel):
    campaign: CampaignResponse
    enqueued_messages: int = 0
    cancelled_queued_messages: int = 0


class MessageSendResultResponse(BaseModel):
    message_id: str
    status: str
    ses_message_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None

    @classmethod
    def from_model(cls, message: Message) -> MessageSendResultResponse:
        return cls(
            message_id=message.id,
            status=message.status,
            ses_message_id=message.ses_message_id,
            error_code=message.error_code,
            error_message=message.error_message,
        )
