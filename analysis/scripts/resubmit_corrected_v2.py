from __future__ import annotations

import argparse
import json
import os
import re
from typing import Any

from src.build_batch import metadata_validation_errors
from src.build_corrected_batch import (
    CORRECTED_BATCH,
    ENDPOINT,
    MODEL,
    ROOT_CAUSE,
    SMOKE_BATCH,
    contains_secret_or_real_action,
    main as build_corrected_files,
    metadata_stats,
    normalize_record_metadata,
    read_jsonl,
    validate_batch_shape,
)
from src.common import CONDITIONS, path, sha256_file, write_text
from src.parse_responses import extract_decision, validate_decision
from src.submit_batch import object_to_dict

EXPERIMENT_ID = "confirmatory_2x2_corrected_v2"
CONFIRMATION_PHRASE = "RUN 4 SMOKE TESTS THEN SUBMIT CORRECTED 2000 BATCH"
STATE_FILE = "batch/submissions/confirmatory_2x2_corrected_v2_state.json"
BATCH_ID_FILE = "batch/submissions/confirmatory_2x2_corrected_v2_BATCH_ID.txt"
REGISTRY_FILE = "batch/submission_registry.json"
SMOKE_OUTPUT = "data/raw_api/smoke_test_corrected_v2_output.jsonl"
SMOKE_FAILURE_REPORT = "reports/smoke_test_corrected_v2_failure.md"
EXPECTED_CORRECTED_SHA256 = "5a18a98614ad5b3abe5d554ee3e6278bffe8deaaf0e33d62344bb44e3b677290"
FAILED_BATCH_ID = "batch_6a42bee0c3a88190b6f498efbdba3d00"


def read_json(rel: str) -> dict[str, Any]:
    target = path(rel)
    if not target.exists():
        return {}
    return json.loads(target.read_text(encoding="utf-8"))


def write_json(rel: str, payload: dict[str, Any]) -> None:
    target = path(rel)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_registry(entry: dict[str, Any]) -> None:
    current = read_json(REGISTRY_FILE)
    submissions = current.get("submissions", []) if isinstance(current, dict) else []
    submissions.append(entry)
    write_json(REGISTRY_FILE, {"submissions": submissions})


def registry_has_sha(file_sha: str) -> str:
    current = read_json(REGISTRY_FILE)
    submissions = current.get("submissions", []) if isinstance(current, dict) else []
    for item in submissions:
        if item.get("input_sha256") == file_sha and item.get("batch_id"):
            return str(item["batch_id"])
    return ""


def duplicate_block_reason(file_sha: str) -> str | None:
    batch_id_file = path(BATCH_ID_FILE)
    if batch_id_file.exists() and batch_id_file.read_text(encoding="utf-8").strip():
        return f"corrected v2 already has batch_id {batch_id_file.read_text(encoding='utf-8').strip()}"
    state = read_json(STATE_FILE)
    if state.get("batch_id"):
        return f"corrected v2 already has batch_id {state['batch_id']}"
    if state.get("submission_in_progress") and not state.get("submission_completed"):
        return "corrected v2 submission is already in progress"
    existing = registry_has_sha(file_sha)
    if existing:
        return f"same SHA-256 already submitted as {existing}"
    return None


def local_controls() -> dict[str, Any]:
    build_summary = build_corrected_files(emit=False)
    materialized = read_jsonl("batch/confirmatory_2000_requests_materialized.jsonl")
    corrected = read_jsonl(CORRECTED_BATCH)
    smoke = read_jsonl(SMOKE_BATCH)
    corrected_sha = sha256_file(path(CORRECTED_BATCH))
    issues: list[str] = []
    if corrected_sha != EXPECTED_CORRECTED_SHA256:
        issues.append(f"corrected SHA-256 mismatch: {corrected_sha}")
    issues.extend(validate_batch_shape(corrected, 2000))
    issues.extend(f"smoke: {issue}" for issue in validate_batch_shape(smoke, 4))
    if [normalize_record_metadata(row) for row in materialized] != corrected:
        issues.append("corrected Batch differs from materialized Batch beyond metadata normalization")
    if [row.get("custom_id") for row in materialized] != [row.get("custom_id") for row in corrected]:
        issues.append("custom IDs changed")
    if [row.get("body", {}).get("input") for row in materialized] != [row.get("body", {}).get("input") for row in corrected]:
        issues.append("prompts changed")
    conditions = {condition: 0 for condition in CONDITIONS}
    for row in corrected:
        parts = row.get("custom_id", "").split("__")
        if len(parts) >= 2 and parts[1] in conditions:
            conditions[parts[1]] += 1
    if any(count != 500 for count in conditions.values()):
        issues.append(f"condition balance failed: {conditions}")
    if not all(row.get("custom_id", "").startswith("SMOKE_DEV_V2_") for row in smoke):
        issues.append("smoke custom_id prefix is not SMOKE_DEV_V2_")
    if any("CON_" in json.dumps(row, ensure_ascii=False) for row in smoke):
        issues.append("smoke file contains confirmatory locked-set identifier")
    corrected_secret, corrected_real_action = contains_secret_or_real_action(CORRECTED_BATCH)
    smoke_secret, smoke_real_action = contains_secret_or_real_action(SMOKE_BATCH)
    if corrected_secret or smoke_secret:
        issues.append("API secret pattern detected")
    if corrected_real_action or smoke_real_action:
        issues.append("real action pattern detected")
    duplicate = duplicate_block_reason(corrected_sha)
    if duplicate:
        issues.append(f"duplicate protection blocked submission: {duplicate}")
    return {
        "build_summary": build_summary,
        "corrected_sha256": corrected_sha,
        "corrected_requests": len(corrected),
        "unique_custom_ids": len({row.get("custom_id") for row in corrected}),
        "non_string_metadata_remaining": metadata_stats(corrected)["non_string"],
        "smoke_requests": len(smoke),
        "smoke_uses_development_data": "YES" if all(row.get("custom_id", "").startswith("SMOKE_DEV_V2_") for row in smoke) else "NO",
        "issues": issues,
    }


def validate_smoke_request_metadata(request: dict[str, Any]) -> None:
    metadata = request.get("body", {}).get("metadata", {})
    issues = metadata_validation_errors(metadata)
    if issues:
        raise ValueError("; ".join(issues))


def smoke_decision_valid(body: dict[str, Any], request: dict[str, Any]) -> tuple[bool, str]:
    if isinstance(body.get("error"), dict):
        return False, str(body["error"].get("message") or body["error"])
    decision = extract_decision({"response": body})
    condition = request["body"]["metadata"]["condition"]
    valid, error = validate_decision(decision, condition)
    if not valid:
        return False, error
    text = json.dumps(body, ensure_ascii=False)
    if re.search(r"booking_endpoint|purchase_endpoint|checkout|stripe|paypal|transaction_url", text, re.I):
        return False, "real action pattern detected in smoke response"
    return True, ""


def write_smoke_failure(custom_id: str, message: str) -> None:
    write_text(
        SMOKE_FAILURE_REPORT,
        f"""
# Corrected v2 smoke test failure

No full Batch upload was attempted. No full Batch was created.

Failed custom_id: `{custom_id}`

Failure: {message}
""",
    )


def run_smoke_tests(client: object) -> list[dict[str, Any]]:
    smoke = read_jsonl(SMOKE_BATCH)
    output_target = path(SMOKE_OUTPUT)
    output_target.parent.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    with output_target.open("w", encoding="utf-8") as f:
        for request in smoke:
            validate_smoke_request_metadata(request)
            custom_id = request["custom_id"]
            try:
                response = client.responses.create(**request["body"])
                body = object_to_dict(response)
                record = {"custom_id": custom_id, "response": body, "error": None}
            except Exception as exc:
                message = str(exc)
                record = {"custom_id": custom_id, "response": None, "error": message}
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                write_smoke_failure(custom_id, message)
                raise SystemExit(message) from exc
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            records.append(record)
            valid, error = smoke_decision_valid(body, request)
            if not valid:
                write_smoke_failure(custom_id, error)
                raise SystemExit(error)
    if len(records) != 4:
        write_smoke_failure("ALL", f"Expected 4 smoke responses, got {len(records)}.")
        raise SystemExit("Expected 4 smoke responses.")
    return records


def submit_corrected_batch(client: object, corrected_sha: str) -> dict[str, Any]:
    duplicate = duplicate_block_reason(corrected_sha)
    if duplicate:
        raise SystemExit(duplicate)
    state = {
        "experiment_id": EXPERIMENT_ID,
        "submission_file": CORRECTED_BATCH,
        "submission_sha256": corrected_sha,
        "submission_in_progress": True,
        "submission_completed": False,
        "input_file_id": "",
        "batch_id": "",
    }
    write_json(STATE_FILE, state)
    with path(CORRECTED_BATCH).open("rb") as f:
        uploaded = client.files.create(file=f, purpose="batch")
    uploaded_dict = object_to_dict(uploaded)
    input_file_id = uploaded_dict.get("id") or getattr(uploaded, "id", "")
    state["input_file_id"] = input_file_id
    write_json(STATE_FILE, state)
    batch = client.batches.create(
        input_file_id=input_file_id,
        endpoint=ENDPOINT,
        completion_window="24h",
        metadata={
            "experiment_id": EXPERIMENT_ID,
            "model": MODEL,
            "requests": "2000",
            "submission_sha256": corrected_sha,
        },
    )
    batch_dict = object_to_dict(batch)
    batch_id = batch_dict.get("id") or getattr(batch, "id", "")
    if not batch_id:
        raise RuntimeError("Batch creation returned no batch_id.")
    state.update({
        "batch_id": batch_id,
        "batch_status": batch_dict.get("status") or getattr(batch, "status", ""),
        "submission_in_progress": False,
        "submission_completed": True,
    })
    write_json(STATE_FILE, state)
    path(BATCH_ID_FILE).parent.mkdir(parents=True, exist_ok=True)
    path(BATCH_ID_FILE).write_text(batch_id + "\n", encoding="utf-8")
    append_registry({
        "experiment_id": EXPERIMENT_ID,
        "input_file": CORRECTED_BATCH,
        "input_sha256": corrected_sha,
        "input_file_id": input_file_id,
        "batch_id": batch_id,
        "batch_status": state.get("batch_status", ""),
    })
    return state


def run(client: object, confirmation: str | None) -> dict[str, Any]:
    summary = local_controls()
    if summary["issues"]:
        raise SystemExit("; ".join(summary["issues"]))
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY NOT SET")
    if os.environ.get("CONFIRM_PAID_RUN") != "YES":
        raise SystemExit("CONFIRM_PAID_RUN must be YES")
    if confirmation != CONFIRMATION_PHRASE:
        raise SystemExit("Confirmation failed; no API call sent.")
    run_smoke_tests(client)
    state = submit_corrected_batch(client, summary["corrected_sha256"])
    return {"summary": summary, "state": state}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirmation")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    from openai import OpenAI

    result = run(OpenAI(), args.confirmation)
    print(json.dumps({
        "experiment_id": EXPERIMENT_ID,
        "batch_id": result["state"].get("batch_id", ""),
        "status": result["state"].get("batch_status", ""),
    }, indent=2))


if __name__ == "__main__":
    main()
