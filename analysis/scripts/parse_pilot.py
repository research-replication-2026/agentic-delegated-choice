from __future__ import annotations

import json
from typing import Any

from src.settings import path


def response_to_dict(response: Any) -> dict[str, Any]:
    if hasattr(response, "model_dump"):
        return response.model_dump()
    if isinstance(response, dict):
        return response
    return json.loads(str(response))


def get_value(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def iter_output_items(raw: Any) -> list[Any]:
    return get_value(raw, "output", []) or []


def iter_content_items(item: Any) -> list[Any]:
    return get_value(item, "content", []) or []


def extract_response_id(raw: Any) -> str | None:
    return get_value(raw, "id")


def extract_output_text(raw: Any) -> str | None:
    output_text = get_value(raw, "output_text")
    if output_text:
        return output_text
    chunks = []
    for item in iter_output_items(raw):
        for content in iter_content_items(item):
            if get_value(content, "type") in {"output_text", "text"} and get_value(content, "text"):
                chunks.append(get_value(content, "text"))
    return "\n".join(chunks) if chunks else None


def parse_arguments(arguments: Any) -> tuple[dict[str, Any] | None, str | None]:
    if isinstance(arguments, dict):
        return arguments, None
    if isinstance(arguments, str):
        try:
            parsed = json.loads(arguments)
        except json.JSONDecodeError as exc:
            return None, f"Function arguments JSON decode error: {exc}"
        if not isinstance(parsed, dict):
            return None, "Function arguments JSON must decode to an object"
        return parsed, None
    return None, f"Function arguments must be a JSON string or object, got {type(arguments).__name__}"


def load_schema(schema_name: str) -> dict[str, Any]:
    with path(f"schemas/{schema_name}.json").open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_json_object(data: dict[str, Any], schema: dict[str, Any], prefix: str) -> list[str]:
    errors: list[str] = []
    required = schema.get("required", [])
    for key in required:
        if key not in data:
            errors.append(f"Missing {prefix} field: {key}")
    properties = schema.get("properties", {})
    for key, spec in properties.items():
        if key not in data:
            continue
        value = data[key]
        expected_type = spec.get("type")
        if expected_type == "string" and not isinstance(value, str):
            errors.append(f"{prefix}.{key} must be string")
        elif expected_type == "number" and (not isinstance(value, (int, float)) or isinstance(value, bool)):
            errors.append(f"{prefix}.{key} must be number")
        elif expected_type == "boolean" and not isinstance(value, bool):
            errors.append(f"{prefix}.{key} must be boolean")
        elif expected_type == "array" and not isinstance(value, list):
            errors.append(f"{prefix}.{key} must be array")
        if "const" in spec and value != spec["const"]:
            errors.append(f"{prefix}.{key} must equal {spec['const']}")
        if "enum" in spec and value not in spec["enum"]:
            errors.append(f"{prefix}.{key} must be one of {spec['enum']}")
    if not schema.get("additionalProperties", True):
        extra = sorted(set(data) - set(properties))
        for key in extra:
            errors.append(f"Unexpected {prefix} field: {key}")
    return errors


def validate_prepare_booking_arguments(arguments: dict[str, Any]) -> list[str]:
    return validate_json_object(arguments, load_schema("prepare_booking"), "prepare_booking")


def validate_recommendation_output(parsed: dict[str, Any]) -> list[str]:
    return validate_json_object(parsed, load_schema("recommendation_output"), "recommendation_output")


def normalize_prepare_booking(tool_call: dict[str, Any]) -> dict[str, Any]:
    args = tool_call["arguments"]
    return {
        "scenario_id": args["scenario_id"],
        "selected_option_id": args["selected_option_id"],
        "ranked_option_ids": [args["selected_option_id"]],
        "criteria_used": [],
        "inferred_preferences": [],
        "alternatives_presented": [],
        "commercial_relationship_disclosed": False,
        "commercial_disclosure_text": "",
        "action_level": "booking_preparation",
        "confirmation_required": args["confirmation_required"],
        "short_rationale": args["short_justification"],
    }


def _tool_from_item(item: Any) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    if get_value(item, "type") not in {"function_call", "tool_call"}:
        return None, errors
    if get_value(item, "name") != "prepare_booking":
        return None, errors
    arguments, arg_error = parse_arguments(get_value(item, "arguments", {}))
    if arg_error:
        return None, [arg_error]
    validation_errors = validate_prepare_booking_arguments(arguments or {})
    if validation_errors:
        return None, validation_errors
    return {
        "name": get_value(item, "name"),
        "call_id": get_value(item, "call_id"),
        "arguments": arguments,
    }, errors


def extract_tool_call(raw: Any) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    for item in iter_output_items(raw):
        tool_call, item_errors = _tool_from_item(item)
        errors.extend(item_errors)
        if tool_call:
            return tool_call, errors
        for content in iter_content_items(item):
            tool_call, content_errors = _tool_from_item(content)
            errors.extend(content_errors)
            if tool_call:
                return tool_call, errors
    return None, errors


def parse_raw_response(raw: Any) -> tuple[dict[str, Any] | None, dict[str, Any] | None, list[str], dict[str, Any]]:
    errors: list[str] = []
    metadata: dict[str, Any] = {
        "output_mode": None,
        "function_call_name": None,
        "function_call_id": None,
        "function_call_arguments": None,
        "response_id": extract_response_id(raw),
    }
    parsed = None
    tool_call = None
    text = extract_output_text(raw)
    if text:
        try:
            parsed = json.loads(text)
            if not isinstance(parsed, dict):
                errors.append("Structured output JSON must be an object")
            else:
                errors.extend(validate_recommendation_output(parsed))
            metadata["output_mode"] = "structured_text"
        except json.JSONDecodeError as exc:
            errors.append(f"JSON decode error: {exc}")
    try:
        tool_call, tool_errors = extract_tool_call(raw)
        errors.extend(tool_errors)
    except Exception as exc:
        errors.append(f"Tool parse error: {exc}")
    if tool_call:
        metadata.update({
            "output_mode": "function_call",
            "function_call_name": tool_call.get("name"),
            "function_call_id": tool_call.get("call_id"),
            "function_call_arguments": tool_call.get("arguments"),
        })
        if parsed is None:
            parsed = normalize_prepare_booking(tool_call)
    if not text and not tool_call:
        errors.append("No structured output text or valid prepare_booking function_call found")
    return parsed, tool_call, errors, metadata
