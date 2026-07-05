import json

from src.openai_client import CONDITIONS
from src.score_pilot import normalize_attempt, observation_key, select_attempts


def parsed_payload(option_id="S01_H1", scenario_id="S01"):
    return {
        "scenario_id": scenario_id,
        "selected_option_id": option_id,
        "ranked_option_ids": [option_id],
        "criteria_used": [],
        "inferred_preferences": [],
        "alternatives_presented": [option_id],
        "commercial_relationship_disclosed": False,
        "commercial_disclosure_text": "",
        "action_level": "recommendation",
        "confirmation_required": True,
        "short_rationale": "Concise rationale.",
    }


def booking_args(option_id="S01_H2", scenario_id="S01"):
    return {
        "scenario_id": scenario_id,
        "selected_option_id": option_id,
        "price_per_night": 145,
        "short_justification": "Concise booking preparation rationale.",
        "confirmation_required": True,
        "simulation_only": True,
    }


def attempt(scenario_id, condition, timestamp, parsed=None, raw=None, response_valid=None, error=None, line=1):
    rec = {
        "scenario_id": scenario_id,
        "condition": condition,
        "timestamp_utc": timestamp,
        "_line_number": line,
        "raw_response": raw,
    }
    if parsed is not None:
        rec["parsed_response"] = parsed
    if response_valid is not None:
        rec["response_valid"] = response_valid
    if error is not None:
        rec["error"] = error
    rec["observation_key"] = observation_key(rec)
    return normalize_attempt(rec)


def selected_for(attempts):
    selected, audit = select_attempts(attempts)
    assert len(selected) == 1
    return selected[0], audit


def test_single_valid_attempt_selected():
    rec = attempt("S01", "neutral_low_agenticity", "2026-01-01T00:00:00Z", parsed=parsed_payload())
    selected, audit = selected_for([rec])
    assert selected["response_valid"] is True
    assert selected["_selected_attempt_number"] == 1
    assert audit["selected_for_analysis"].sum() == 1


def test_invalid_then_valid_keeps_valid_latest():
    first = attempt("S01", "neutral_low_agenticity", "2026-01-01T00:00:00Z", response_valid=False, error="bad")
    second = attempt("S01", "neutral_low_agenticity", "2026-01-01T00:01:00Z", parsed=parsed_payload(), line=2)
    selected, _ = selected_for([first, second])
    assert selected is second
    assert selected["_selected_attempt_number"] == 2
    assert selected["_had_previous_failure"] is True


def test_multiple_valid_attempts_keeps_most_recent():
    first = attempt("S01", "neutral_low_agenticity", "2026-01-01T00:00:00Z", parsed=parsed_payload("S01_H1"))
    second = attempt("S01", "neutral_low_agenticity", "2026-01-01T00:01:00Z", parsed=parsed_payload("S01_H2"), line=2)
    selected, _ = selected_for([first, second])
    assert selected is second
    assert selected["parsed_response"]["selected_option_id"] == "S01_H2"


def test_only_invalid_attempts_keeps_last_and_marks_invalid():
    first = attempt("S01", "neutral_low_agenticity", "2026-01-01T00:00:00Z", response_valid=False, error="bad")
    second = attempt("S01", "neutral_low_agenticity", "2026-01-01T00:01:00Z", response_valid=False, error="still bad", line=2)
    selected, _ = selected_for([first, second])
    assert selected is second
    assert selected["response_valid"] is False


def test_valid_function_call_without_text_is_valid_attempt():
    raw = {
        "id": "resp_fc",
        "output": [{
            "type": "function_call",
            "name": "prepare_booking",
            "call_id": "call_fc",
            "arguments": json.dumps(booking_args()),
        }],
    }
    rec = attempt("S01", "neutral_high_agenticity", "2026-01-01T00:00:00Z", raw=raw)
    selected, _ = selected_for([rec])
    assert selected["response_valid"] is True
    assert selected["output_mode"] == "function_call"
    assert selected["parsed_response"]["selected_option_id"] == "S01_H2"


def test_thirty_four_historical_lines_reduce_to_twenty_observations():
    attempts = []
    line = 1
    for scenario_idx in range(1, 6):
        scenario_id = f"S{scenario_idx:02d}"
        for condition in CONDITIONS:
            attempts.append(attempt(scenario_id, condition, f"2026-01-01T00:{line:02d}:00Z", parsed=parsed_payload(scenario_id=scenario_id), line=line))
            line += 1
    duplicate_keys = [(f"S{idx:02d}", condition) for idx in range(1, 5) for condition in CONDITIONS[:3]]
    duplicate_keys += [("S05", CONDITIONS[0]), ("S05", CONDITIONS[1])]
    assert len(duplicate_keys) == 14
    for scenario_id, condition in duplicate_keys:
        attempts.append(attempt(scenario_id, condition, f"2026-01-01T01:{line:02d}:00Z", parsed=parsed_payload(option_id=f"{scenario_id}_H2", scenario_id=scenario_id), line=line))
        line += 1
    selected, audit = select_attempts(attempts)
    assert len(attempts) == 34
    assert len(audit) == 34
    assert len(selected) == 20
    assert len({rec["observation_key"] for rec in selected}) == 20
