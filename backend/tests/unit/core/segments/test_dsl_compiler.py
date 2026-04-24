from __future__ import annotations

import pytest
from sqlalchemy import select

from libs.core.contacts.models import Contact
from libs.core.errors import ValidationError
from libs.core.segments.dsl import SegmentDslCompiler


def test_dsl_compiler_accepts_typed_nested_predicate() -> None:
    compiler = SegmentDslCompiler()
    predicate = {
        "op": "and",
        "conditions": [
            {"op": "eq", "field": "contact.email_domain", "value": "dispatch.test"},
            {"op": "gt", "field": "contact.total_opens", "value": 1},
            {
                "op": "or",
                "conditions": [
                    {"op": "contains", "field": "contact.first_name", "value": "kh"},
                    {"op": "in", "field": "subscription.status", "value": ["subscribed"]},
                ],
            },
        ],
    }

    expression = compiler.compile_predicate(predicate)
    stmt = select(Contact.id).where(expression)
    compiled = str(stmt.compile())
    assert "contacts.email_domain" in compiled
    assert "contacts.total_opens" in compiled


def test_dsl_compiler_rejects_unknown_field() -> None:
    compiler = SegmentDslCompiler()
    with pytest.raises(ValidationError):
        compiler.compile_predicate({"op": "eq", "field": "contact.password_hash", "value": "x"})


def test_dsl_compiler_rejects_unknown_operator() -> None:
    compiler = SegmentDslCompiler()
    with pytest.raises(ValidationError):
        compiler.compile_predicate({"op": "like_sql", "field": "contact.email", "value": "%@x.com"})


def test_dsl_compiler_rejects_hostile_sql_payload() -> None:
    compiler = SegmentDslCompiler()
    hostile = "dispatch.test' OR 1=1 --"
    expression = compiler.compile_predicate(
        {"op": "eq", "field": "contact.email_domain", "value": hostile}
    )
    compiled = str(select(Contact.id).where(expression).compile())
    assert hostile not in compiled


@pytest.mark.parametrize(
    "payload",
    [
        {"op": "gt", "field": "contact.email", "value": 3},
        {"op": "contains", "field": "contact.total_opens", "value": "1"},
        {"op": "in", "field": "contact.email", "value": []},
        {"op": "not", "field": "contact.email", "value": "x"},
    ],
)
def test_dsl_compiler_rejects_invalid_shapes(payload: dict[str, object]) -> None:
    compiler = SegmentDslCompiler()
    with pytest.raises(ValidationError):
        compiler.compile_predicate(payload)
