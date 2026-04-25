from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from typing import cast as typing_cast

from sqlalchemy import String, and_, cast, func, not_, or_
from sqlalchemy.sql.elements import ColumnElement

from libs.core.contacts.models import Contact, Preference, SubscriptionStatus
from libs.core.errors import ValidationError

_LEAF_OPERATORS = {"eq", "neq", "in", "gt", "lt", "contains"}
_LOGICAL_OPERATORS = {"and", "or", "not"}
_SUPPORTED_OPERATORS = _LEAF_OPERATORS | _LOGICAL_OPERATORS

_STRING = "string"
_INTEGER = "integer"
_STRING_LIST = "string_list"


@dataclass(frozen=True)
class FieldSpec:
    expression: Any
    value_type: str


def default_field_allow_list() -> dict[str, FieldSpec]:
    fields: dict[str, FieldSpec] = {
        "email": FieldSpec(Contact.email, _STRING),
        "contact.email": FieldSpec(Contact.email, _STRING),
        "email_domain": FieldSpec(Contact.email_domain, _STRING),
        "contact.email_domain": FieldSpec(Contact.email_domain, _STRING),
        "first_name": FieldSpec(Contact.first_name, _STRING),
        "contact.first_name": FieldSpec(Contact.first_name, _STRING),
        "last_name": FieldSpec(Contact.last_name, _STRING),
        "contact.last_name": FieldSpec(Contact.last_name, _STRING),
        "company": FieldSpec(Contact.company, _STRING),
        "contact.company": FieldSpec(Contact.company, _STRING),
        "title": FieldSpec(Contact.title, _STRING),
        "contact.title": FieldSpec(Contact.title, _STRING),
        "country_code": FieldSpec(Contact.country_code, _STRING),
        "contact.country_code": FieldSpec(Contact.country_code, _STRING),
        "timezone": FieldSpec(Contact.timezone, _STRING),
        "contact.timezone": FieldSpec(Contact.timezone, _STRING),
        "lifecycle_status": FieldSpec(Contact.lifecycle_status, _STRING),
        "contact.lifecycle_status": FieldSpec(Contact.lifecycle_status, _STRING),
        "validation_status": FieldSpec(Contact.validation_status, _STRING),
        "contact.validation_status": FieldSpec(Contact.validation_status, _STRING),
        "total_sends": FieldSpec(Contact.total_sends, _INTEGER),
        "contact.total_sends": FieldSpec(Contact.total_sends, _INTEGER),
        "total_opens": FieldSpec(Contact.total_opens, _INTEGER),
        "contact.total_opens": FieldSpec(Contact.total_opens, _INTEGER),
        "total_clicks": FieldSpec(Contact.total_clicks, _INTEGER),
        "contact.total_clicks": FieldSpec(Contact.total_clicks, _INTEGER),
        "total_replies": FieldSpec(Contact.total_replies, _INTEGER),
        "contact.total_replies": FieldSpec(Contact.total_replies, _INTEGER),
        "preferences.language": FieldSpec(Preference.language, _STRING),
        "preferences.max_frequency_per_week": FieldSpec(
            Preference.max_frequency_per_week,
            _INTEGER,
        ),
        "preferences.campaign_types": FieldSpec(Preference.campaign_types, _STRING_LIST),
        "subscription.status": FieldSpec(SubscriptionStatus.status, _STRING),
        "subscription.channel": FieldSpec(SubscriptionStatus.channel, _STRING),
    }
    return fields


class SegmentDslCompiler:
    def __init__(self, *, field_allow_list: dict[str, FieldSpec] | None = None) -> None:
        self._field_allow_list = field_allow_list or default_field_allow_list()

    def compile_predicate(self, predicate: Mapping[str, object]) -> ColumnElement[bool]:
        if not isinstance(predicate, Mapping):
            raise ValidationError("Segment DSL predicate must be a JSON object")
        return self._compile_node(dict(predicate))

    @property
    def allowed_fields(self) -> set[str]:
        return set(self._field_allow_list.keys())

    def _compile_node(self, node: Mapping[str, object]) -> ColumnElement[bool]:
        operator = node.get("op")
        if not isinstance(operator, str):
            raise ValidationError("Segment DSL node requires a string operator")
        operator_lower = operator.lower()
        if operator_lower not in _SUPPORTED_OPERATORS:
            raise ValidationError(f"Unsupported segment operator: {operator}")

        if operator_lower in {"and", "or"}:
            conditions = node.get("conditions")
            if not isinstance(conditions, list) or not conditions:
                raise ValidationError(f"Operator '{operator_lower}' requires non-empty conditions")
            compiled_conditions = [self._compile_child(item) for item in conditions]
            if operator_lower == "and":
                return and_(*compiled_conditions)
            return or_(*compiled_conditions)

        if operator_lower == "not":
            condition = node.get("condition")
            if not isinstance(condition, Mapping):
                raise ValidationError("Operator 'not' requires an object condition")
            return not_(self._compile_node(dict(condition)))

        field_name = node.get("field")
        if not isinstance(field_name, str):
            raise ValidationError(f"Operator '{operator_lower}' requires a field")
        field_spec = self._field_allow_list.get(field_name)
        if field_spec is None:
            raise ValidationError(f"Unsupported segment field: {field_name}")

        value = node.get("value")
        if operator_lower == "eq":
            return typing_cast(
                ColumnElement[bool],
                field_spec.expression == self._coerce_single_value(field_spec, value),
            )
        if operator_lower == "neq":
            return typing_cast(
                ColumnElement[bool],
                field_spec.expression != self._coerce_single_value(field_spec, value),
            )
        if operator_lower == "in":
            values = self._coerce_list_value(field_spec, value)
            return typing_cast(ColumnElement[bool], field_spec.expression.in_(values))
        if operator_lower == "gt":
            self._assert_operator_type(operator_lower, field_spec, allowed={_INTEGER})
            coerced = self._coerce_single_value(field_spec, value)
            return typing_cast(ColumnElement[bool], field_spec.expression > coerced)
        if operator_lower == "lt":
            self._assert_operator_type(operator_lower, field_spec, allowed={_INTEGER})
            coerced = self._coerce_single_value(field_spec, value)
            return typing_cast(ColumnElement[bool], field_spec.expression < coerced)
        if operator_lower == "contains":
            return self._compile_contains(field_spec, value)

        raise ValidationError(f"Unsupported segment operator: {operator_lower}")

    def _compile_child(self, child: object) -> ColumnElement[bool]:
        if not isinstance(child, Mapping):
            raise ValidationError("Segment DSL child nodes must be objects")
        return self._compile_node(dict(child))

    def _assert_operator_type(
        self,
        operator: str,
        field_spec: FieldSpec,
        *,
        allowed: set[str],
    ) -> None:
        if field_spec.value_type not in allowed:
            raise ValidationError(
                f"Operator '{operator}' is not allowed for this field type"
            )

    def _coerce_single_value(self, field_spec: FieldSpec, value: object) -> object:
        if field_spec.value_type == _STRING:
            if not isinstance(value, str):
                raise ValidationError("Segment value must be a string")
            cleaned = value.strip()
            if not cleaned:
                raise ValidationError("Segment value must not be empty")
            return cleaned

        if field_spec.value_type == _INTEGER:
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValidationError("Segment value must be an integer")
            return value

        if field_spec.value_type == _STRING_LIST:
            if not isinstance(value, str):
                raise ValidationError("Segment value must be a string")
            cleaned = value.strip()
            if not cleaned:
                raise ValidationError("Segment value must not be empty")
            return cleaned

        raise ValidationError("Unsupported field type in segment allow-list")

    def _coerce_list_value(self, field_spec: FieldSpec, value: object) -> list[object]:
        if not isinstance(value, list) or not value:
            raise ValidationError("Operator 'in' requires a non-empty list")
        coerced = [self._coerce_single_value(field_spec, item) for item in value]
        return coerced

    def _compile_contains(self, field_spec: FieldSpec, value: object) -> ColumnElement[bool]:
        coerced = self._coerce_single_value(field_spec, value)
        if not isinstance(coerced, str):
            raise ValidationError("Operator 'contains' requires a string value")
        self._assert_operator_type(
            "contains",
            field_spec,
            allowed={_STRING, _STRING_LIST},
        )
        expression_text = cast(field_spec.expression, String)
        if field_spec.value_type == _STRING:
            return typing_cast(
                ColumnElement[bool],
                func.lower(expression_text).like(f"%{coerced.lower()}%"),
            )
        return typing_cast(
            ColumnElement[bool],
            func.lower(expression_text).like(f'%"{coerced.lower()}"%'),
        )
