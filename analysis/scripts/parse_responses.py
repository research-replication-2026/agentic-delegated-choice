from __future__ import annotations

import csv
import json
from typing import Any

from src.common import AUDIT_COLUMNS, expected_action_fields, path, read_json, select_latest_valid_attempt, write_csv
from src.provenance import REAL_ERRORS, REAL_OUTPUT, line_count, write_validated_provenance

PARSED_COLUMNS = [
    "observation_key", "attempt_id", "scenario_id", "condition", "repetition",
    "model", "response_valid", "error", "selected_option_id", "ranked_option_ids",
    "criteria_used", "alternatives_presented", "commercial_relationship_disclosed",
    "commercial_disclosure_text", "action_level", "action_prepared",
    "confirmation_required", "simulation_only", "latency_seconds", "input_tokens",
    "output_tokens",
]


def extract_decision(rec: dict[str, Any]) -> dict[str, Any] | None:
    if isinstance(rec.get("response"), dict) and "selected_option_id" in rec["response"]:
        return rec["response"]
    response = rec.get("response") or rec.get("raw_response") or {}
    for item in response.get("output", []) if isinstance(response, dict) else []:
        if item.get("type") in {"function_call", "tool_call"} and item.get("name") == "submit_agentic_decision":
            args = item.get("arguments", {})
            if isinstance(args, str):
                return json.loads(args)
            if isinstance(args, dict):
                return args
    return None


def validate_decision(decision: dict[str, Any] | None, condition: str) -> tuple[bool, str]:
    if not isinstance(decision, dict):
        return False, "No submit_agentic_decision payload found"
    required = [
        "scenario_id", "condition", "selected_option_id", "ranked_option_ids",
        "criteria_used", "alternatives_presented", "commercial_relationship_disclosed",
        "commercial_disclosure_text", "action_level", "action_prepared",
        "confirmation_required", "short_rationale", "simulation_only",
    ]
    missing = [key for key in required if key not in decision]
    if missing:
        return False, f"Missing fields: {missing}"
    action_level, action_prepared, confirmation_required = expected_action_fields(condition)
    if decision["simulation_only"] is not True:
        return False, "simulation_only is not true"
    if decision["action_level"] != action_level:
        return False, "Wrong action_level"
    if bool(decision["action_prepared"]) != action_prepared:
        return False, "Wrong action_prepared"
    if bool(decision["confirmation_required"]) != confirmation_required:
        return False, "Wrong confirmation_required"
    return True, ""


def parse_file(raw_rel: str, prefix: str) -> None:
    if prefix != "confirmatory" or "mock" in raw_rel:
        print("REAL BATCH DATA REQUIRED")
        raise SystemExit("REAL BATCH DATA REQUIRED: mock parsing is disabled.")
    raw = path(raw_rel)
    attempts = []
    if raw.exists():
        with raw.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                if not line.strip():
                    continue
                rec = json.loads(line)
                decision = extract_decision(rec)
                valid, error = validate_decision(decision, rec.get("condition", ""))
                row = {
                    "observation_key": rec.get("observation_key", ""),
                    "attempt_id": rec.get("attempt_id", f"line-{line_no}"),
                    "attempt_number": rec.get("attempt_number", 1),
                    "scenario_id": rec.get("scenario_id", decision.get("scenario_id", "") if decision else ""),
                    "condition": rec.get("condition", decision.get("condition", "") if decision else ""),
                    "repetition": rec.get("repetition", ""),
                    "model": rec.get("model", ""),
                    "response_valid": valid,
                    "error": error,
                    "selected_option_id": decision.get("selected_option_id", "") if decision else "",
                    "ranked_option_ids": "|".join(decision.get("ranked_option_ids", [])) if decision else "",
                    "criteria_used": "|".join(decision.get("criteria_used", [])) if decision else "",
                    "alternatives_presented": "|".join(decision.get("alternatives_presented", [])) if decision else "",
                    "commercial_relationship_disclosed": decision.get("commercial_relationship_disclosed", "") if decision else "",
                    "commercial_disclosure_text": decision.get("commercial_disclosure_text", "") if decision else "",
                    "action_level": decision.get("action_level", "") if decision else "",
                    "action_prepared": decision.get("action_prepared", "") if decision else "",
                    "confirmation_required": decision.get("confirmation_required", "") if decision else "",
                    "simulation_only": decision.get("simulation_only", "") if decision else "",
                    "latency_seconds": rec.get("latency_seconds", ""),
                    "input_tokens": rec.get("input_tokens", ""),
                    "output_tokens": rec.get("output_tokens", ""),
                    "line_number": line_no,
                }
                attempts.append(row)
    selected, audit = select_latest_valid_attempt(attempts)
    write_csv(f"data/processed/{prefix}_parsed.csv", selected, PARSED_COLUMNS)
    audit_name = "confirmatory_attempts_audit.csv" if prefix == "confirmatory" else f"{prefix}_attempts_audit.csv"
    write_csv(f"data/processed/{audit_name}", audit, AUDIT_COLUMNS)


def load_plan_by_observation() -> dict[str, dict[str, str]]:
    with path("data/locked/confirmatory_run_plan.csv").open("r", encoding="utf-8") as f:
        return {row["observation_key"]: row for row in csv.DictReader(f)}


def load_batch_metadata() -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    for rel in ["batch/batch_status.json", "batch/submission_state.json"]:
        target = path(rel)
        if target.exists():
            try:
                metadata.update(read_json(rel))
            except json.JSONDecodeError:
                pass
    return metadata


def iter_real_batch_lines(raw_rel: str = REAL_OUTPUT) -> tuple[list[dict[str, Any]], int]:
    raw = path(raw_rel)
    if not raw.exists() or raw.stat().st_size == 0:
        print("REAL BATCH DATA REQUIRED")
        raise SystemExit(f"REAL BATCH DATA REQUIRED: {raw_rel} is missing or empty.")
    records: list[dict[str, Any]] = []
    http_200 = 0
    with raw.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as exc:
                print("REAL BATCH DATA REQUIRED")
                raise SystemExit(f"REAL BATCH DATA REQUIRED: line {line_no} is invalid JSON: {exc}") from exc
            response = rec.get("response")
            if not isinstance(response, dict) or "status_code" not in response:
                print("REAL BATCH DATA REQUIRED")
                raise SystemExit("REAL BATCH DATA REQUIRED: file is not an OpenAI Batch output JSONL.")
            if int(response.get("status_code") or 0) == 200:
                http_200 += 1
            records.append(rec)
    if http_200 <= 0:
        print("REAL BATCH DATA REQUIRED")
        raise SystemExit("REAL BATCH DATA REQUIRED: no HTTP 200 response found.")
    return records, http_200


def parse_confirmatory_batch_output(raw_rel: str = REAL_OUTPUT) -> dict[str, int]:
    records, http_200 = iter_real_batch_lines(raw_rel)
    plan = load_plan_by_observation()
    attempts = []
    for line_no, rec in enumerate(records, start=1):
        custom_id = rec.get("custom_id", "")
        plan_row = plan.get(custom_id, {})
        response = rec.get("response") or {}
        status_code = int(response.get("status_code") or 0)
        body = response.get("body") if isinstance(response.get("body"), dict) else {}
        decision = extract_decision({"response": body}) if status_code == 200 else None
        condition = plan_row.get("condition", "")
        valid, error = validate_decision(decision, condition) if status_code == 200 else (False, f"HTTP status {status_code}")
        usage = body.get("usage") if isinstance(body, dict) else {}
        if not isinstance(usage, dict):
            usage = {}
        attempts.append({
            "observation_key": custom_id,
            "attempt_id": rec.get("id", f"line-{line_no}"),
            "attempt_number": 1,
            "scenario_id": plan_row.get("scenario_id", decision.get("scenario_id", "") if decision else ""),
            "condition": condition or (decision.get("condition", "") if decision else ""),
            "repetition": plan_row.get("repetition", ""),
            "model": body.get("model", "") if isinstance(body, dict) else "",
            "response_valid": valid,
            "error": error,
            "selected_option_id": decision.get("selected_option_id", "") if decision else "",
            "ranked_option_ids": "|".join(decision.get("ranked_option_ids", [])) if decision else "",
            "criteria_used": "|".join(decision.get("criteria_used", [])) if decision else "",
            "alternatives_presented": "|".join(decision.get("alternatives_presented", [])) if decision else "",
            "commercial_relationship_disclosed": decision.get("commercial_relationship_disclosed", "") if decision else "",
            "commercial_disclosure_text": decision.get("commercial_disclosure_text", "") if decision else "",
            "action_level": decision.get("action_level", "") if decision else "",
            "action_prepared": decision.get("action_prepared", "") if decision else "",
            "confirmation_required": decision.get("confirmation_required", "") if decision else "",
            "simulation_only": decision.get("simulation_only", "") if decision else "",
            "latency_seconds": "",
            "input_tokens": usage.get("input_tokens", ""),
            "output_tokens": usage.get("output_tokens", ""),
            "line_number": line_no,
        })
    selected, audit = select_latest_valid_attempt(attempts)
    write_csv("data/processed/confirmatory_parsed.csv", selected, PARSED_COLUMNS)
    write_csv("data/processed/confirmatory_attempts_audit.csv", audit, AUDIT_COLUMNS)
    metadata = load_batch_metadata()
    write_validated_provenance(
        batch_id=str(metadata.get("id") or metadata.get("batch_id") or ""),
        output_file_id=str(metadata.get("output_file_id") or ""),
        response_count=http_200,
        error_count=line_count(REAL_ERRORS),
        extra={"valid_response_count": len(selected), "output_lines": len(records)},
    )
    return {"output_lines": len(records), "http_200": http_200, "valid_responses": len(selected)}


def main() -> None:
    result = parse_confirmatory_batch_output()
    print(f"Real Batch responses parsed: {result['valid_responses']} valid responses.")


if __name__ == "__main__":
    main()
