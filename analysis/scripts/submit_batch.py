from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.common import path, sha256_file, write_text
from src.build_batch import metadata_validation_errors

SUBMISSION_BATCH = "batch/confirmatory_2000_requests_corrected_v2.jsonl"
EXPECTED_SHA256 = "5a18a98614ad5b3abe5d554ee3e6278bffe8deaaf0e33d62344bb44e3b677290"
EXPECTED_MODEL = "gpt-5.4-mini"
EXPECTED_ENDPOINT = "/v1/responses"
EXPECTED_REQUESTS = 2000
STATE_FILE = "batch/submission_state.json"
LAST_BATCH_ID = "batch/LAST_BATCH_ID.txt"
SUBMISSION_REGISTRY = "batch/submission_registry.json"
EXPERIMENT_STATES_DIR = "batch/submissions"
PREFLIGHT_REPORT = "reports/provider_submission_preflight.md"
CONFIRMATION_PHRASE = "SUBMIT CONFIRMATORY 2X2 PAID BATCH"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def object_to_dict(obj: Any) -> dict[str, Any]:
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    return {k: v for k, v in vars(obj).items() if not k.startswith("_")}


def atomic_write_json(rel: str, payload: dict[str, Any]) -> None:
    target = path(rel)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(target.parent), delete=False) as tmp:
        json.dump(payload, tmp, ensure_ascii=False, indent=2)
        tmp.write("\n")
        tmp_name = tmp.name
    Path(tmp_name).replace(target)


def load_state() -> dict[str, Any]:
    target = path(STATE_FILE)
    if not target.exists():
        return {}
    return json.loads(target.read_text(encoding="utf-8"))


def existing_batch_id() -> str:
    state = load_state()
    state_batch = str(state.get("batch_id") or "").strip()
    text_file = path(LAST_BATCH_ID)
    file_batch = text_file.read_text(encoding="utf-8").strip() if text_file.exists() else ""
    return state_batch or file_batch


def read_registry() -> list[dict[str, Any]]:
    target = path(SUBMISSION_REGISTRY)
    if not target.exists():
        return []
    data = json.loads(target.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    return data.get("submissions", []) if isinstance(data, dict) else []


def write_registry(entries: list[dict[str, Any]]) -> None:
    atomic_write_json(SUBMISSION_REGISTRY, {"submissions": entries})


def existing_batch_for_sha(file_hash: str) -> str:
    for entry in read_registry():
        if entry.get("input_sha256") == file_hash and entry.get("batch_id"):
            return str(entry["batch_id"])
    state = load_state()
    if state.get("submission_sha256") == file_hash and state.get("batch_id"):
        return str(state["batch_id"])
    return ""


def experiment_state_file(experiment_id: str) -> str:
    if experiment_id == "confirmatory_2x2":
        return STATE_FILE
    return f"{EXPERIMENT_STATES_DIR}/{experiment_id}_submission_state.json"


def experiment_last_batch_file(experiment_id: str) -> str:
    if experiment_id == "confirmatory_2x2":
        return LAST_BATCH_ID
    return f"batch/LAST_BATCH_ID_{experiment_id}.txt"


def expected_request_count(input_file: str) -> int:
    return 4 if "smoke" in Path(input_file).name else EXPECTED_REQUESTS


def read_requests(input_file: str | None = None) -> tuple[list[dict[str, Any]], list[str]]:
    input_file = input_file or SUBMISSION_BATCH
    target = path(input_file)
    errors: list[str] = []
    rows: list[dict[str, Any]] = []
    if not target.exists():
        return rows, [f"Missing submission file: {input_file}"]
    with target.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                errors.append(f"Line {line_no} invalid JSON: {exc}")
    return rows, errors


def validate_submission_inputs(
    require_paid_guard: bool = False,
    run_tests: bool = True,
    input_file: str | None = None,
    experiment_id: str = "confirmatory_2x2",
) -> dict[str, Any]:
    input_file = input_file or SUBMISSION_BATCH
    critical: list[str] = []
    sdk_available = False
    try:
        import openai  # noqa: F401
        sdk_available = True
    except Exception as exc:
        critical.append(f"OpenAI SDK import failed: {exc}")

    api_key_detected = bool(os.environ.get("OPENAI_API_KEY", "").strip())
    if not api_key_detected:
        critical.append("OPENAI_API_KEY NOT SET")
    if require_paid_guard and os.environ.get("CONFIRM_PAID_RUN") != "YES":
        critical.append("CONFIRM_PAID_RUN must be YES.")

    file_hash = sha256_file(path(input_file)) if path(input_file).exists() else ""
    expected_sha = EXPECTED_SHA256 if input_file == SUBMISSION_BATCH else ""
    if expected_sha and file_hash != expected_sha:
        critical.append(f"Submission file SHA-256 mismatch: {file_hash}")

    duplicate_batch_id = existing_batch_for_sha(file_hash) if file_hash else ""
    if duplicate_batch_id:
        critical.append(f"SUBMISSION BLOCKED: FILE SHA-256 ALREADY SUBMITTED AS {duplicate_batch_id}")

    rows, json_errors = read_requests(input_file)
    critical.extend(json_errors)
    custom_ids = [row.get("custom_id", "") for row in rows]
    urls = {row.get("url", "") for row in rows}
    models = {row.get("body", {}).get("model", "") for row in rows}
    placeholders = sum(1 for row in rows if row.get("body", {}).get("model") == "${OPENAI_MODEL}")
    text = path(input_file).read_text(encoding="utf-8") if path(input_file).exists() else ""
    expected_requests = expected_request_count(input_file)

    if len(rows) != expected_requests:
        critical.append(f"Expected {expected_requests} requests, got {len(rows)}.")
    if len(set(custom_ids)) != expected_requests:
        critical.append(f"Expected {expected_requests} unique custom_id values, got {len(set(custom_ids))}.")
    if urls != {EXPECTED_ENDPOINT}:
        critical.append(f"All request URLs must be {EXPECTED_ENDPOINT}; observed {sorted(urls)}.")
    if models != {EXPECTED_MODEL}:
        critical.append(f"All body.model values must be {EXPECTED_MODEL}; observed {sorted(models)}.")
    if placeholders:
        critical.append(f"Unresolved model placeholders remain: {placeholders}.")
    if "" in models:
        critical.append("At least one body.model is empty.")
    if "previous_response_id" in text:
        critical.append("previous_response_id appears in submission file.")
    if re.search(r"sk-[A-Za-z0-9]{20,}", text):
        critical.append("API secret pattern detected in submission file.")
    if re.search(r"booking_endpoint|purchase_endpoint|checkout|stripe|paypal|transaction_url", text, re.I):
        critical.append("Real action/payment endpoint pattern detected in submission file.")
    for line_no, row in enumerate(rows, start=1):
        for issue in metadata_validation_errors(row.get("body", {}).get("metadata", {})):
            critical.append(f"line {line_no}: {issue}")

    tests_passed = False
    test_output = ""
    if run_tests:
        test_env = dict(os.environ)
        test_env["PYTHONDONTWRITEBYTECODE"] = "1"
        test_env["PYTHONPATH"] = "."
        result = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
            cwd=path("."),
            text=True,
            capture_output=True,
            env=test_env,
        )
        tests_passed = result.returncode == 0
        test_output = (result.stdout + "\n" + result.stderr)[-2000:]
        if not tests_passed:
            critical.append("Automated tests failed.")

    return {
        "sdk_available": sdk_available,
        "api_key_detected": api_key_detected,
        "submission_file": input_file,
        "submission_sha256": file_hash,
        "model": EXPECTED_MODEL,
        "endpoint": EXPECTED_ENDPOINT,
        "requests": len(rows),
        "unique_custom_ids": len(set(custom_ids)),
        "existing_batch_id": duplicate_batch_id or "NONE",
        "experiment_id": experiment_id,
        "placeholders": placeholders,
        "tests_passed": tests_passed,
        "test_output": test_output,
        "critical": critical,
        "decision": "GO" if not critical else "NO-GO",
    }


def write_preflight_report(summary: dict[str, Any]) -> None:
    failures = "\n".join(f"- {item}" for item in summary["critical"]) or "- None."
    report = f"""
# Provider submission preflight

No API call was sent. No file was uploaded. No Batch was submitted.

| Metric | Value |
| --- | --- |
| SDK available | {summary['sdk_available']} |
| API key detected | {summary['api_key_detected']} |
| Submission file | {summary['submission_file']} |
| Submission SHA-256 | `{summary['submission_sha256']}` |
| Model | {summary['model']} |
| Endpoint | {summary['endpoint']} |
| Requests | {summary['requests']} |
| Unique custom IDs | {summary['unique_custom_ids']} |
| Existing batch ID | {summary['existing_batch_id']} |
| Preflight tests | {summary['tests_passed']} |
| Critical failures | {len(summary['critical'])} |
| Decision | {summary['decision']} |

## Critical Failures

{failures}

## Official API Shape Used

The adapter uses the OpenAI Python SDK: `client.files.create(file=..., purpose="batch")` followed by `client.batches.create(input_file_id=..., endpoint="/v1/responses", completion_window="24h", metadata=...)`.
"""
    write_text(PREFLIGHT_REPORT, report)


def initial_state(input_file_id: str | None = None, batch_id: str | None = None, status: str | None = None) -> dict[str, Any]:
    return {
        "submission_file": SUBMISSION_BATCH,
        "submission_sha256": EXPECTED_SHA256,
        "model": EXPECTED_MODEL,
        "request_count": str(EXPECTED_REQUESTS),
        "input_file_id": input_file_id or "",
        "batch_id": batch_id or "",
        "batch_status": status or "",
        "created_at_utc": utc_now(),
        "last_checked_at_utc": utc_now(),
        "submission_attempted": True,
        "submission_completed": bool(batch_id),
    }


def submission_state(
    *,
    input_file: str,
    input_sha256: str,
    experiment_id: str,
    request_count: int,
    input_file_id: str | None = None,
    batch_id: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    return {
        "experiment_id": experiment_id,
        "submission_file": input_file,
        "submission_sha256": input_sha256,
        "model": EXPECTED_MODEL,
        "request_count": str(request_count),
        "input_file_id": input_file_id or "",
        "batch_id": batch_id or "",
        "batch_status": status or "",
        "created_at_utc": utc_now(),
        "last_checked_at_utc": utc_now(),
        "submission_attempted": True,
        "submission_completed": bool(batch_id),
    }


def submit(
    client: object | None = None,
    confirmation_reader=None,
    run_tests: bool = True,
    confirmation: str | None = None,
    input_file: str | None = None,
    experiment_id: str = "confirmatory_2x2",
) -> dict[str, Any]:
    input_file = input_file or SUBMISSION_BATCH
    summary = validate_submission_inputs(
        require_paid_guard=True,
        run_tests=run_tests,
        input_file=input_file,
        experiment_id=experiment_id,
    )
    if "OPENAI_API_KEY NOT SET" in summary["critical"]:
        write_preflight_report(summary)
        raise SystemExit("OPENAI_API_KEY NOT SET")
    if summary["critical"]:
        write_preflight_report(summary)
        raise SystemExit("; ".join(summary["critical"]))

    phrase = confirmation
    if phrase is None and confirmation_reader is not None:
        phrase = confirmation_reader()
    if phrase != CONFIRMATION_PHRASE:
        raise SystemExit("Confirmation failed; no batch submitted.")

    if client is None:
        from openai import OpenAI
        client = OpenAI()
    input_sha256 = sha256_file(path(input_file))
    state_file = experiment_state_file(experiment_id)
    last_batch_file = experiment_last_batch_file(experiment_id)
    state = submission_state(
        input_file=input_file,
        input_sha256=input_sha256,
        experiment_id=experiment_id,
        request_count=expected_request_count(input_file),
    )
    atomic_write_json(state_file, state)
    try:
        with path(input_file).open("rb") as f:
            uploaded = client.files.create(file=f, purpose="batch")
        uploaded_dict = object_to_dict(uploaded)
        input_file_id = uploaded_dict.get("id") or getattr(uploaded, "id", "")
        state.update({"input_file_id": input_file_id, "last_checked_at_utc": utc_now()})
        atomic_write_json(state_file, state)

        batch = client.batches.create(
            input_file_id=input_file_id,
            endpoint=EXPECTED_ENDPOINT,
            completion_window="24h",
            metadata={
                "experiment": experiment_id,
                "requests": str(expected_request_count(input_file)),
                "model": EXPECTED_MODEL,
                "submission_sha256": input_sha256,
            },
        )
        batch_dict = object_to_dict(batch)
        batch_id = batch_dict.get("id") or getattr(batch, "id", "")
        status = batch_dict.get("status") or getattr(batch, "status", "")
        path(last_batch_file).parent.mkdir(parents=True, exist_ok=True)
        path(last_batch_file).write_text(batch_id + "\n", encoding="utf-8")
        state.update({
            "batch_id": batch_id,
            "batch_status": status,
            "last_checked_at_utc": utc_now(),
            "submission_completed": True,
        })
        atomic_write_json(state_file, state)
        entries = read_registry()
        entries.append({
            "experiment_id": experiment_id,
            "input_file": input_file,
            "input_sha256": input_sha256,
            "input_file_id": input_file_id,
            "batch_id": batch_id,
            "batch_status": status,
            "created_at_utc": state["created_at_utc"],
        })
        write_registry(entries)
        return state
    except Exception as exc:
        state.update({
            "last_checked_at_utc": utc_now(),
            "submission_completed": False,
            "error": str(exc),
        })
        atomic_write_json(state_file, state)
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--confirmation")
    parser.add_argument("--input-file", default=SUBMISSION_BATCH)
    parser.add_argument("--experiment-id", default="confirmatory_2x2")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.preflight:
        summary = validate_submission_inputs(
            require_paid_guard=False,
            run_tests=True,
            input_file=args.input_file,
            experiment_id=args.experiment_id,
        )
        write_preflight_report(summary)
        print(json.dumps({
            "decision": summary["decision"],
            "critical_failures": len(summary["critical"]),
            "api_calls_sent": 0,
            "file_uploaded": "NO",
            "batch_submitted": "NO",
        }, indent=2))
        return
    submit(confirmation=args.confirmation, input_file=args.input_file, experiment_id=args.experiment_id)


if __name__ == "__main__":
    main()
