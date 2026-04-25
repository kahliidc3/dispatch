from __future__ import annotations

from typing import Any

import pytest

from libs.core.auth.schemas import CurrentActor
from libs.core.errors import ConflictError, PermissionDeniedError, ValidationError
from libs.core.templates.schemas import (
    TemplateCreateRequest,
    TemplatePreviewRequest,
    TemplateVersionCreateRequest,
)

AuthTestContext = Any
UserFactory = Any


async def _create_actor(
    auth_user_factory: UserFactory,
    *,
    email: str,
    role: str,
) -> CurrentActor:
    user = await auth_user_factory(email=email, password="password-value-123", role=role)
    return CurrentActor(actor_type="user", user=user)


@pytest.mark.asyncio
async def test_template_lifecycle_versioning_and_archive_rules(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    admin_actor = await _create_actor(
        auth_user_factory,
        email="admin-template-service@dispatch.test",
        role="admin",
    )
    user_actor = await _create_actor(
        auth_user_factory,
        email="user-template-service@dispatch.test",
        role="user",
    )

    with pytest.raises(PermissionDeniedError):
        await auth_test_context.template_service.create_template(
            actor=user_actor,
            payload=TemplateCreateRequest(
                name="Denied",
                description=None,
                category=None,
                subject="Hello {{contact.first_name}}",
                body_text="Plan {{contact.preferences.plan}}",
                body_html=None,
                spintax_enabled=True,
            ),
            ip_address=None,
            user_agent=None,
        )

    created = await auth_test_context.template_service.create_template(
        actor=admin_actor,
        payload=TemplateCreateRequest(
            name="Welcome",
            description="Primary welcome template",
            category="onboarding",
            subject="Hello {{contact.first_name}}",
            body_text="Plan: {{contact.preferences.plan}}",
            body_html="<p>Hello {{contact.first_name}}</p>",
            spintax_enabled=True,
        ),
        ip_address=None,
        user_agent=None,
    )
    assert created.head_version_number == 1
    assert created.is_archived is False
    assert created.versions[0].version_number == 1
    assert created.versions[0].merge_tags == [
        "contact.first_name",
        "contact.preferences.plan",
    ]

    versioned = await auth_test_context.template_service.create_template_version(
        actor=admin_actor,
        template_id=created.template.id,
        payload=TemplateVersionCreateRequest(
            subject="Updated {{contact.first_name}}",
            body_text="Hi {{contact.first_name}} {{contact.last_name}}",
            body_html=None,
            spintax_enabled=False,
        ),
        ip_address=None,
        user_agent=None,
    )
    assert versioned.head_version_number == 2
    assert len(versioned.versions) == 2
    assert versioned.versions[0].is_published is False
    assert versioned.versions[1].is_published is True

    preview = await auth_test_context.template_service.preview_template(
        actor=admin_actor,
        template_id=created.template.id,
        payload=TemplatePreviewRequest(
            version_number=2,
            sample_contact={"first_name": "Khalid", "last_name": "Coder"},
        ),
    )
    assert preview.version_number == 2
    assert "Khalid Coder" in preview.rendered_body_text

    archived = await auth_test_context.template_service.archive_template(
        actor=admin_actor,
        template_id=created.template.id,
        ip_address=None,
        user_agent=None,
    )
    assert archived.is_archived is True
    assert archived.category == "onboarding"

    with pytest.raises(ConflictError):
        await auth_test_context.template_service.create_template_version(
            actor=admin_actor,
            template_id=created.template.id,
            payload=TemplateVersionCreateRequest(
                subject="Should fail",
                body_text="Archived template",
                body_html=None,
                spintax_enabled=False,
            ),
            ip_address=None,
            user_agent=None,
        )


@pytest.mark.asyncio
async def test_template_version_is_immutable(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    admin_actor = await _create_actor(
        auth_user_factory,
        email="admin-template-immutable@dispatch.test",
        role="admin",
    )
    created = await auth_test_context.template_service.create_template(
        actor=admin_actor,
        payload=TemplateCreateRequest(
            name="Immutable",
            description=None,
            category=None,
            subject="Immutable {{contact.first_name}}",
            body_text="Body",
            body_html=None,
            spintax_enabled=False,
        ),
        ip_address=None,
        user_agent=None,
    )

    with pytest.raises(ConflictError):
        await auth_test_context.template_service.assert_version_is_immutable(
            actor=admin_actor,
            template_id=created.template.id,
            version_number=1,
        )


@pytest.mark.asyncio
async def test_template_subject_crlf_and_missing_preview_fields_are_rejected(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    admin_actor = await _create_actor(
        auth_user_factory,
        email="admin-template-validate@dispatch.test",
        role="admin",
    )

    with pytest.raises(ValidationError):
        await auth_test_context.template_service.create_template(
            actor=admin_actor,
            payload=TemplateCreateRequest(
                name="CRLF",
                description=None,
                category=None,
                subject="Hello\r\nBcc:bad@dispatch.test",
                body_text="Safe body",
                body_html=None,
                spintax_enabled=False,
            ),
            ip_address=None,
            user_agent=None,
        )

    created = await auth_test_context.template_service.create_template(
        actor=admin_actor,
        payload=TemplateCreateRequest(
            name="Strict undefined",
            description=None,
            category=None,
            subject="Hi {{contact.first_name}}",
            body_text="Body",
            body_html=None,
            spintax_enabled=False,
        ),
        ip_address=None,
        user_agent=None,
    )

    with pytest.raises(ValidationError):
        await auth_test_context.template_service.preview_template(
            actor=admin_actor,
            template_id=created.template.id,
            payload=TemplatePreviewRequest(sample_contact={}),
        )
