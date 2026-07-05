from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path
from typing import Any

from src.common import path, sha256_file, write_text

ORIGINAL_BATCH = "batch/confirmatory_2000_requests.jsonl"
MATERIALIZED_BATCH = "batch/confirmatory_2000_requests_materialized.jsonl"
EXPECTED_ORIGINAL_SHA256 = "9c89339e0a3c90813528aae6f13e475597cd745359fd553ea560281e9a7b4448"
REPORT = "reports/materialized_batch_validation_report.md"


def read_jsonl(rel: str) -> list[dict[str, Any]]:
    target = path(rel)
    if not target.exists():
        return []
    rows = []
    with target.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def neutralized(record: dict[str, Any]) -> dict[str, Any]:
    clone = json.loads(json.dumps(record, ensure_ascii=False))
    clone.get("body", {})["model"] = "__MODEL_NEUTRALIZED__"
    return clone


def has_real_action(text: str) -> bool:
    return bool(re.search(r"booking_endpoint|purchase_endpoint|checkout|stripe|paypal|transaction_url", text, re.I))


def write_report(summary: dict[str, Any], critical: list[str]) -> None:
    failure_md = "\n".join(f"- {item}" for item in critical) or "- None."
    report = f"""
# Materialized batch validation report

## Summary

| Metric | Value |
| --- | --- |
| OPENAI_MODEL defined | {summary['openai_model_defined']} |
| Model source file | {summary['model_source_file']} |
| Concrete model | {summary['concrete_model']} |
| Original batch unchanged | {summary['original_batch_unchanged']} |
| Original batch SHA-256 | `{summary['original_batch_sha256']}` |
| Materialized batch | {summary['materialized_batch']} |
| Materialized batch SHA-256 | `{summary['materialized_batch_sha256']}` |
| JSONL rows | {summary['jsonl_rows']} |
| Unique custom IDs | {summary['unique_custom_ids']} |
| Unresolved model placeholders | {summary['unresolved_model_placeholders']} |
| Distinct concrete models | {summary['distinct_concrete_models']} |
| Only body.model changed | {summary['only_body_model_changed']} |
| API secret detected | {summary['api_secret_detected']} |
| Real action possible | {summary['real_action_possible']} |
| Critical failures | {len(critical)} |
| Decision | {summary['decision']} |

## Critical Failures

{failure_md}

No API call was sent and no batch was submitted.
"""
    write_text(REPORT, report)


def write_summary_csv(summary: dict[str, Any]) -> None:
    target = path("results/tables/materialized_batch_validation_summary.csv")
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["metric", "value"])
        writer.writeheader()
        for key, value in summary.items():
            writer.writerow({"metric": key, "value": value})


def validate_materialized(original: list[dict[str, Any]], materialized: list[dict[str, Any]], model: str) -> tuple[dict[str, Any], list[str]]:
    critical: list[str] = []
    original_hash = sha256_file(path(ORIGINAL_BATCH)) if path(ORIGINAL_BATCH).exists() else ""
    materialized_exists = path(MATERIALIZED_BATCH).exists()
    materialized_hash = sha256_file(path(MATERIALIZED_BATCH)) if materialized_exists else ""
    original_unchanged = original_hash == EXPECTED_ORIGINAL_SHA256

    if not original_unchanged:
        critical.append("Original batch SHA-256 changed.")
    if not model:
        critical.append("OPENAI_MODEL is not defined or is empty.")
    if len(materialized) != 2000:
        critical.append(f"Materialized batch must contain exactly 2000 requests; observed {len(materialized)}.")

    custom_ids = [rec.get("custom_id", "") for rec in materialized]
    unique_custom_ids = len(set(custom_ids))
    if unique_custom_ids != 2000:
        critical.append(f"Materialized batch must contain 2000 unique custom_id values; observed {unique_custom_ids}.")

    original_ids = [rec.get("custom_id", "") for rec in original]
    if custom_ids and set(custom_ids) != set(original_ids):
        critical.append("Materialized custom_id set differs from the original batch.")

    models = {rec.get("body", {}).get("model", "") for rec in materialized}
    unresolved = sum(1 for rec in materialized if rec.get("body", {}).get("model") == "${OPENAI_MODEL}")
    if unresolved:
        critical.append(f"Materialized batch still contains {unresolved} unresolved model placeholders.")
    if model and models != {model}:
        critical.append(f"Materialized batch must contain exactly one concrete model {model!r}; observed {sorted(models)}.")

    only_model_changed = False
    if len(original) == len(materialized) == 2000:
        only_model_changed = all(neutralized(a) == neutralized(b) for a, b in zip(original, materialized))
        if not only_model_changed:
            critical.append("At least one materialized request differs from original beyond body.model.")

    text = path(MATERIALIZED_BATCH).read_text(encoding="utf-8") if materialized_exists else ""
    secret_detected = bool(re.search(r"sk-[A-Za-z0-9]{20,}", text))
    real_action_possible = has_real_action(text)
    if secret_detected:
        critical.append("API-secret-like pattern detected in materialized batch.")
    if real_action_possible:
        critical.append("Real action endpoint/payment pattern detected in materialized batch.")

    summary = {
        "openai_model_defined": bool(model),
        "model_source_file": os.environ.get("MODEL_SOURCE_FILE", ""),
        "concrete_model": model if model else "NOT SET",
        "original_batch_unchanged": "YES" if original_unchanged else "NO",
        "original_batch_sha256": original_hash,
        "materialized_batch": MATERIALIZED_BATCH if materialized_exists else "NOT CREATED",
        "materialized_batch_sha256": materialized_hash,
        "jsonl_rows": len(materialized),
        "unique_custom_ids": unique_custom_ids,
        "unresolved_model_placeholders": unresolved,
        "distinct_concrete_models": len(models - {""}),
        "only_body_model_changed": "YES" if only_model_changed else "NO",
        "api_secret_detected": secret_detected,
        "real_action_possible": real_action_possible,
        "decision": "GO" if not critical else "NO-GO",
    }
    return summary, critical


def main() -> None:
    model = os.environ.get("OPENAI_MODEL", "").strip()
    original = read_jsonl(ORIGINAL_BATCH)

    if model:
        target = path(MATERIALIZED_BATCH)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as f:
            for rec in original:
                clone = json.loads(json.dumps(rec, ensure_ascii=False))
                clone.setdefault("body", {})["model"] = model
                f.write(json.dumps(clone, ensure_ascii=False) + "\n")

    materialized = read_jsonl(MATERIALIZED_BATCH)
    summary, critical = validate_materialized(original, materialized, model)
    write_report(summary, critical)
    write_summary_csv(summary)
    print(json.dumps({"decision": summary["decision"], "critical_failures": len(critical)}, indent=2))


if __name__ == "__main__":
    main()
