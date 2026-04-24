from __future__ import annotations

from typing import Any

import pytest

from libs.core.auth.schemas import CurrentActor
from libs.core.errors import ValidationError
from libs.core.templates.schemas import TemplateCreateRequest, TemplatePreviewRequest

AuthTestContext = Any
UserFactory = Any


async def _create_admin_actor(auth_user_factory: UserFactory) -> CurrentActor:
    user = await auth_user_factory(
        email="admin-template-sandbox@dispatch.test",
        password="sandbox-password-value",
        role="admin",
    )
    return CurrentActor(actor_type="user", user=user)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dangerous_body",
    [
        "{{ contact.__class__ }}",
        "{{ cycler.__init__.__globals__.os.popen('id').read() }}",
        "{% import os %}",
        "{{ contact['first_name'] }}",
        "{{ contact.first_name | upper }}",
    ],
)
async def test_renderer_rejects_dangerous_or_non_grammar_constructs(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
    dangerous_body: str,
) -> None:
    actor = await _create_admin_actor(auth_user_factory)

    with pytest.raises(ValidationError):
        await auth_test_context.template_service.create_template(
            actor=actor,
            payload=TemplateCreateRequest(
                name="Dangerous template",
                description=None,
                category=None,
                subject="Safe {{contact.first_name}}",
                body_text=dangerous_body,
                body_html=None,
                spintax_enabled=False,
            ),
            ip_address=None,
            user_agent=None,
        )


@pytest.mark.asyncio
async def test_preview_renders_unicode_safely(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    actor = await _create_admin_actor(auth_user_factory)
    created = await auth_test_context.template_service.create_template(
        actor=actor,
        payload=TemplateCreateRequest(
            name="Unicode template",
            description=None,
            category=None,
            subject="مرحبا {{contact.first_name}}",
            body_text="Welcome {{contact.first_name}} 🌍",
            body_html="<p>مرحبا {{contact.first_name}}</p>",
            spintax_enabled=False,
        ),
        ip_address=None,
        user_agent=None,
    )

    preview = await auth_test_context.template_service.preview_template(
        actor=actor,
        template_id=created.template.id,
        payload=TemplatePreviewRequest(sample_contact={"first_name": "خالد"}),
    )
    assert preview.rendered_subject == "مرحبا خالد"
    assert preview.rendered_body_text == "Welcome خالد 🌍"
    assert preview.rendered_body_html == "<p>مرحبا خالد</p>"
