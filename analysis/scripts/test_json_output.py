import json
from types import SimpleNamespace

from src.parse_pilot import parse_raw_response


def test_parse_structured_output_text():
    payload = {
        "scenario_id": "S01",
        "selected_option_id": "S01_H1",
        "ranked_option_ids": ["S01_H1", "S01_H2", "S01_H3"],
        "criteria_used": ["calm"],
        "inferred_preferences": ["quiet"],
        "alternatives_presented": ["S01_H1", "S01_H2", "S01_H3"],
        "commercial_relationship_disclosed": False,
        "commercial_disclosure_text": "",
        "action_level": "recommendation",
        "confirmation_required": True,
        "short_rationale": "Best fit.",
    }
    raw = {"output": [{"content": [{"type": "output_text", "text": json.dumps(payload)}]}]}
    parsed, tool, errors, metadata = parse_raw_response(raw)
    assert parsed["selected_option_id"] == "S01_H1"
    assert tool is None
    assert errors == []
    assert metadata["output_mode"] == "structured_text"


def booking_args(**overrides):
    payload = {
        "scenario_id": "S03",
        "selected_option_id": "S03_H2",
        "price_per_night": 165,
        "short_justification": "Strong fit for the requested accessible work trip.",
        "confirmation_required": True,
        "simulation_only": True,
    }
    payload.update(overrides)
    return payload


def test_parse_high_agenticity_function_call_only_json_string():
    raw = {
        "id": "resp_123",
        "output": [{
            "type": "function_call",
            "name": "prepare_booking",
            "call_id": "call_123",
            "arguments": json.dumps(booking_args()),
        }],
    }
    parsed, tool, errors, metadata = parse_raw_response(raw)
    assert errors == []
    assert tool["name"] == "prepare_booking"
    assert tool["call_id"] == "call_123"
    assert parsed["scenario_id"] == "S03"
    assert parsed["selected_option_id"] == "S03_H2"
    assert parsed["ranked_option_ids"] == ["S03_H2"]
    assert parsed["action_level"] == "booking_preparation"
    assert parsed["confirmation_required"] is True
    assert parsed["short_rationale"] == "Strong fit for the requested accessible work trip."
    assert metadata["output_mode"] == "function_call"
    assert metadata["function_call_name"] == "prepare_booking"
    assert metadata["function_call_id"] == "call_123"
    assert metadata["function_call_arguments"]["selected_option_id"] == "S03_H2"
    assert metadata["response_id"] == "resp_123"


def test_parse_high_agenticity_function_call_only_dict_arguments():
    raw = {
        "output": [{
            "type": "function_call",
            "name": "prepare_booking",
            "call_id": "call_456",
            "arguments": booking_args(selected_option_id="S03_H1"),
        }],
    }
    parsed, tool, errors, metadata = parse_raw_response(raw)
    assert errors == []
    assert parsed["selected_option_id"] == "S03_H1"
    assert tool["arguments"]["price_per_night"] == 165
    assert metadata["output_mode"] == "function_call"


def test_parse_function_call_object_shape():
    raw = SimpleNamespace(
        id="resp_obj",
        output=[
            SimpleNamespace(
                type="function_call",
                name="prepare_booking",
                call_id="call_obj",
                arguments=json.dumps(booking_args(scenario_id="S04", selected_option_id="S04_H2")),
            )
        ],
    )
    parsed, tool, errors, metadata = parse_raw_response(raw)
    assert errors == []
    assert parsed["scenario_id"] == "S04"
    assert parsed["selected_option_id"] == "S04_H2"
    assert tool["call_id"] == "call_obj"
    assert metadata["response_id"] == "resp_obj"


def test_invalid_function_call_is_error():
    raw = {
        "output": [{
            "type": "function_call",
            "name": "prepare_booking",
            "call_id": "call_bad",
            "arguments": booking_args(simulation_only=False),
        }],
    }
    parsed, tool, errors, metadata = parse_raw_response(raw)
    assert parsed is None
    assert tool is None
    assert any("simulation_only" in error for error in errors)
    assert metadata["output_mode"] is None


def test_absence_of_text_and_function_call_is_error():
    raw = {"id": "resp_empty", "output": []}
    parsed, tool, errors, metadata = parse_raw_response(raw)
    assert parsed is None
    assert tool is None
    assert errors == ["No structured output text or valid prepare_booking function_call found"]
    assert metadata["response_id"] == "resp_empty"
