from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List
from urllib.parse import urlparse

from ..core.enums import FieldDataType
from ..core.errors import ValidationError


def validate_entry_payload(*, fields: List[Dict[str, Any]], data: Dict[str, Any], partial: bool = False) -> Dict[str, Any]:
    field_map = {field["key"]: field for field in fields if field.get("is_active", True)}
    unknown = sorted(set(data.keys()) - set(field_map.keys()))
    if unknown:
        raise ValidationError([{"field": key, "message": "Unknown field"} for key in unknown])

    normalized: Dict[str, Any] = {}
    errors: List[Dict[str, str]] = []
    for key, field in field_map.items():
        present = key in data
        rules = field.get("validation_json") or {}
        if not present:
            if partial:
                continue
            if field.get("default_value") is not None:
                normalized[key] = field["default_value"]
            elif field.get("is_required") and not rules.get("allow_null", False):
                errors.append({"field": key, "message": "Field is required"})
            continue

        value = data[key]
        try:
            normalized[key] = _validate_field_value(field, value)
        except ValidationError as exc:
            detail = exc.detail if isinstance(exc.detail, list) else [{"field": key, "message": str(exc.detail)}]
            errors.extend(detail)

    if errors:
        raise ValidationError(errors)
    return normalized


def _validate_field_value(field: Dict[str, Any], value: Any) -> Any:
    key = field["key"]
    rules = field.get("validation_json") or {}
    settings = field.get("settings_json") or {}
    data_type = FieldDataType(field["data_type"])

    if value is None:
        if rules.get("allow_null"):
            return None
        raise ValidationError([{"field": key, "message": "Null is not allowed"}])

    validators = {
        FieldDataType.TEXT: _validate_text,
        FieldDataType.LONG_TEXT: _validate_text,
        FieldDataType.INTEGER: _validate_integer,
        FieldDataType.DECIMAL: _validate_decimal,
        FieldDataType.BOOLEAN: _validate_boolean,
        FieldDataType.DATE: _validate_date,
        FieldDataType.DATETIME: _validate_datetime,
        FieldDataType.EMAIL: _validate_email,
        FieldDataType.URL: _validate_url,
        FieldDataType.SELECT: _validate_select,
        FieldDataType.MULTI_SELECT: _validate_multi_select,
        FieldDataType.REFERENCE: _validate_reference,
        FieldDataType.FILE: _validate_file,
        FieldDataType.JSON: _validate_json,
    }
    return validators[data_type](key, value, rules, settings)


def _validate_text(key: str, value: Any, rules: Dict[str, Any], _settings: Dict[str, Any]) -> str:
    if not isinstance(value, str):
        raise ValidationError([{"field": key, "message": "Expected string"}])
    return _apply_text_rules(key, value, rules)


def _apply_text_rules(key: str, value: str, rules: Dict[str, Any]) -> str:
    if "min_length" in rules and len(value) < int(rules["min_length"]):
        raise ValidationError([{"field": key, "message": f"Minimum length is {rules['min_length']}"}])
    if "max_length" in rules and len(value) > int(rules["max_length"]):
        raise ValidationError([{"field": key, "message": f"Maximum length is {rules['max_length']}"}])
    if rules.get("regex") and re.fullmatch(rules["regex"], value) is None:
        raise ValidationError([{"field": key, "message": "Value does not match regex"}])
    return value


def _validate_integer(key: str, value: Any, rules: Dict[str, Any], _settings: Dict[str, Any]) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError([{"field": key, "message": "Expected integer"}])
    if "min" in rules and value < int(rules["min"]):
        raise ValidationError([{"field": key, "message": f"Minimum value is {rules['min']}"}])
    if "max" in rules and value > int(rules["max"]):
        raise ValidationError([{"field": key, "message": f"Maximum value is {rules['max']}"}])
    return value


def _validate_decimal(key: str, value: Any, rules: Dict[str, Any], _settings: Dict[str, Any]) -> str:
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValidationError([{"field": key, "message": "Expected decimal-compatible value"}])
    if "min" in rules and decimal_value < Decimal(str(rules["min"])):
        raise ValidationError([{"field": key, "message": f"Minimum value is {rules['min']}"}])
    if "max" in rules and decimal_value > Decimal(str(rules["max"])):
        raise ValidationError([{"field": key, "message": f"Maximum value is {rules['max']}"}])
    return str(decimal_value)


def _validate_boolean(key: str, value: Any, _rules: Dict[str, Any], _settings: Dict[str, Any]) -> bool:
    if not isinstance(value, bool):
        raise ValidationError([{"field": key, "message": "Expected boolean"}])
    return value


def _validate_date(key: str, value: Any, _rules: Dict[str, Any], _settings: Dict[str, Any]) -> str:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str):
        try:
            return date.fromisoformat(value).isoformat()
        except ValueError:
            pass
    raise ValidationError([{"field": key, "message": "Expected ISO date"}])


def _validate_datetime(key: str, value: Any, _rules: Dict[str, Any], _settings: Dict[str, Any]) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
        except ValueError:
            pass
    raise ValidationError([{"field": key, "message": "Expected ISO datetime"}])


def _validate_email(key: str, value: Any, rules: Dict[str, Any], settings: Dict[str, Any]) -> str:
    value = _validate_text(key, value, rules, settings)
    if "@" not in value or value.startswith("@") or value.endswith("@"):
        raise ValidationError([{"field": key, "message": "Expected email"}])
    return value


def _validate_url(key: str, value: Any, rules: Dict[str, Any], settings: Dict[str, Any]) -> str:
    value = _validate_text(key, value, rules, settings)
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValidationError([{"field": key, "message": "Expected URL"}])
    return value


def _get_options(rules: Dict[str, Any]) -> List[Any]:
    options = rules.get("options") or []
    if not isinstance(options, list):
        raise ValidationError([{"field": "_schema", "message": "Validation options must be a list"}])
    return options


def _validate_select(key: str, value: Any, rules: Dict[str, Any], _settings: Dict[str, Any]) -> Any:
    if value not in _get_options(rules):
        raise ValidationError([{"field": key, "message": "Value is not in allowed options"}])
    return value


def _validate_multi_select(key: str, value: Any, rules: Dict[str, Any], _settings: Dict[str, Any]) -> List[Any]:
    if not isinstance(value, list):
        raise ValidationError([{"field": key, "message": "Expected list"}])
    options = set(_get_options(rules))
    invalid = [item for item in value if item not in options]
    if invalid:
        raise ValidationError([{"field": key, "message": f"Invalid options: {invalid}"}])
    return value


def _validate_reference(key: str, value: Any, _rules: Dict[str, Any], settings: Dict[str, Any]) -> Any:
    if settings.get("multiple"):
        if not isinstance(value, list) or any(not isinstance(item, int) for item in value):
            raise ValidationError([{"field": key, "message": "Expected list of entry ids"}])
        return value
    if not isinstance(value, int):
        raise ValidationError([{"field": key, "message": "Expected entry id"}])
    return value


def _validate_file(key: str, value: Any, _rules: Dict[str, Any], settings: Dict[str, Any]) -> Any:
    if settings.get("multiple"):
        if not isinstance(value, list) or any(not isinstance(item, int) for item in value):
            raise ValidationError([{"field": key, "message": "Expected list of attachment ids"}])
        return value
    if not isinstance(value, int):
        raise ValidationError([{"field": key, "message": "Expected attachment id"}])
    return value


def _validate_json(key: str, value: Any, _rules: Dict[str, Any], _settings: Dict[str, Any]) -> Any:
    return value
