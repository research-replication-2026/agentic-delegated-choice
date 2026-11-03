from __future__ import annotations

import json
import re
from collections import Counter
from typing import Any

from src.build_batch import build_request, metadata_validation_errors, stringify_metadata
from src.build_run_plan import shuffled_visible_options, user_prompt
from src.common import CONDITIONS, canonical_json, path, read_csv, read_json, sha256_file, sha256_text, write_text

MATERIALIZED_BATCH = "batch/confirmatory_2000_requests_materialized.jsonl"
CORRECTED_BATCH = "batch/confirmatory_2000_requests_corrected_v2.jsonl"
SMOKE_BATCH = "batch/smoke_test_4_requests_corrected_v2.jsonl"
MODEL = "gpt-5.4-mini"
ENDPOINT = "/v1/responses"
LOCKED_SCENARIOS_SHA256 = "1fd1df266514b52723d66b4c128db6bb0b2e358caabd08b824d4409d58d0cb0d"
LOCKED_RUN_PLAN_SHA256 = "35714495d2e3ed72523692c15d6d54f2eb972d26aff4f87a3cbe7bb0439fbd92"
FAILED_BATCH_ID = "batch_6a42bee0c3a88190b6f498efbdba3d00"
ROOT_CAUSE = "Invalid type for 'metadata.expected_action_prepared': expected a string, but got a boolean instead."


def read_jsonl(rel: str) -> list[dict[str, Any]]:
    with path(rel).open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(rel: str, rows: list[dict[str, Any]]) -> None:
    target = path(rel)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def normalize_record_metadata(record: dict[str, Any]) -> dict[str, Any]:
    clone = json.loads(json.dumps(record, ensure_ascii=False))
    body = clone.setdefault("body", {})
    body["metadata"] = stringify_metadata(body.get("metadata", {}))
    return clone


def metadata_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    checked = 0
    non_string = 0
    fields: Counter[str] = Counter()
    issues: list[str] = []
    for line_no, rec in enumerate(rows, start=1):
        metadata = rec.get("body", {}).get("metadata", {})
        checked += len(metadata) if isinstance(metadata, dict) else 0
        for key, value in metadata.items() if isinstance(metadata, dict) else []:
            fields[str(key)] += 1
            if not isinstance(value, str):
                non_string += 1
        for issue in metadata_validation_errors(metadata):
            issues.append(f"line {line_no}: {issue}")
    return {"checked": checked, "non_string": non_string, "fields": dict(fields), "issues": issues}


def conversion_stats(original_rows: list[dict[str, Any]]) -> dict[str, Any]:
    converted = 0
    fields: Counter[str] = Counter()
    for rec in original_rows:
        metadata = rec.get("body", {}).get("metadata", {})
        if not isinstance(metadata, dict):
            continue
        for key, value in metadata.items():
            if value is None or not isinstance(value, str):
                converted += 1
                fields[str(key)] += 1
    return {"converted": converted, "fields": dict(fields)}


def build_corrected_requests() -> list[dict[str, Any]]:
    previous = read_jsonl(MATERIALIZED_BATCH)
    return [normalize_record_metadata(row) for row in previous]


def build_corrected_requests_from_locked_plan() -> list[dict[str, Any]]:
    plan = read_csv("data/locked/confirmatory_run_plan.csv")
    tool_schema = read_json("schemas/submit_agentic_decision.json")
    rows: list[dict[str, Any]] = []
    for row in plan:
        request, _instruction = build_request(row, tool_schema, MODEL)
        rows.append(request)
    return rows


def smoke_rows() -> list[dict[str, Any]]:
    scenario = read_json("data/development/development_scenarios_internal.json")["scenarios"][0]
    seed = int(sha256_text("smoke_v2:DEV_HOT_001:1")[:12], 16)
    visible_options, mapping, partner_position = shuffled_visible_options(scenario, 1, seed)
    inverse_mapping = {v: k for k, v in mapping.items()}
    prompt = user_prompt(scenario, visible_options)
    rows: list[dict[str, Any]] = []
    for condition in CONDITIONS:
        rows.append({
            "observation_key": f"SMOKE_DEV_V2_{scenario['scenario_id']}__{condition}__rep01",
            "scenario_id": scenario["scenario_id"],
            "condition": condition,
            "repetition": "1",
            "domain": scenario["domain"],
            "commission_rate": scenario["commission_rate"],
            "utility_gap": scenario["utility_gap"],
            "optimal_option_id": scenario["optimal_option_id"],
            "partner_option_id": scenario["partner_option_id"],
            "visible_optimal_option_id": mapping[scenario["optimal_option_id"]],
            "visible_partner_option_id": mapping[scenario["partner_option_id"]],
            "partner_position": partner_position,
            "random_seed": seed,
            "visible_to_canonical_json": canonical_json(inverse_mapping),
            "visible_options_json": canonical_json(visible_options),
            "user_prompt": prompt,
        })
    return rows


def build_smoke_requests() -> list[dict[str, Any]]:
    tool_schema = read_json("schemas/submit_agentic_decision.json")
    return [build_request(row, tool_schema, MODEL)[0] for row in smoke_rows()]


def contains_secret_or_real_action(rel: str) -> tuple[bool, bool]:
    text = path(rel).read_text(encoding="utf-8") if path(rel).exists() else ""
    secret = bool(re.search(r"sk-[A-Za-z0-9]{20,}", text))
    real_action = bool(re.search(r"booking_endpoint|purchase_endpoint|checkout|stripe|paypal|transaction_url", text, re.I))
    return secret, real_action


def validate_batch_shape(rows: list[dict[str, Any]], expected_count: int) -> list[str]:
    issues: list[str] = []
    if len(rows) != expected_count:
        issues.append(f"expected {expected_count} requests, got {len(rows)}")
    custom_ids = [row.get("custom_id", "") for row in rows]
    if len(set(custom_ids)) != expected_count:
        issues.append(f"expected {expected_count} unique custom_id values, got {len(set(custom_ids))}")
    if {row.get("url") for row in rows} != {ENDPOINT}:
        issues.append("unexpected endpoint")
    if {row.get("body", {}).get("model") for row in rows} != {MODEL}:
        issues.append("unexpected model")
    if sum(1 for row in rows if row.get("body", {}).get("model") == "${OPENAI_MODEL}"):
        issues.append("unresolved OPENAI_MODEL placeholder")
    metadata_issues = metadata_stats(rows)["issues"]
    issues.extend(metadata_issues)
    return issues


def write_reports(summary: dict[str, Any]) -> None:
    converted_fields = ", ".join(f"{k}={v}" for k, v in sorted(summary["converted_fields"].items())) or "None"
    metadata_fields = ", ".join(sorted(summary["metadata_fields"])) or "None"
    fix_report = f"""
# Metadata type fix report

## Cause

The first Batch `{FAILED_BATCH_ID}` failed with 0 successful responses and 2000 errors.

Root cause: {ROOT_CAUSE}

The protocol, locked scenarios, locked run plan, prompts, custom IDs, model, endpoint and output schema were not changed.

## Correction

Only `body.metadata` values were normalized for API submission. Boolean values are now serialized as strings (`true` / `false`), numeric values as stable text, strings are kept unchanged, and `None` values are omitted.

Converted metadata values: {summary['metadata_values_converted']}

Converted fields: {converted_fields}

Metadata fields checked: {metadata_fields}

No API call was sent. No Batch was submitted.
"""
    validation_report = f"""
# Corrected Batch validation report

| Metric | Value |
| --- | --- |
| Previous materialized Batch | `{MATERIALIZED_BATCH}` |
| Previous SHA-256 | `{summary['previous_sha256']}` |
| Corrected Batch | `{CORRECTED_BATCH}` |
| Corrected SHA-256 | `{summary['corrected_sha256']}` |
| Requests | {summary['corrected_requests']} |
| Unique custom IDs | {summary['unique_custom_ids']} |
| Metadata values checked | {summary['metadata_values_checked']} |
| Non-string metadata values remaining | {summary['non_string_metadata_remaining']} |
| Prompts unchanged | {summary['prompts_unchanged']} |
| Custom IDs unchanged | {summary['custom_ids_unchanged']} |
| Normalized files equivalent | {summary['normalized_files_equivalent']} |
| Locked scenarios unchanged | {summary['locked_scenarios_unchanged']} |
| Locked run plan unchanged | {summary['locked_run_plan_unchanged']} |
| Critical failures | {summary['critical_failures']} |
| Decision | {summary['decision']} |

The only authorized difference from the previous materialized Batch is conversion of `body.metadata` values to strings.
"""
    smoke_report = f"""
# Smoke test preflight

| Metric | Value |
| --- | --- |
| Smoke test file | `{SMOKE_BATCH}` |
| Requests | {summary['smoke_requests']} |
| Unique custom IDs | {summary['smoke_unique_custom_ids']} |
| Uses development data | {summary['smoke_uses_development_data']} |
| Metadata values are strings | {summary['smoke_metadata_strings']} |
| Model | {MODEL} |
| Endpoint | {ENDPOINT} |
| API secret detected | {summary['smoke_secret_detected']} |
| Real action pattern detected | {summary['smoke_real_action_detected']} |

No API call was sent. No Batch was submitted.
"""
    corrected_v2_preflight = f"""
# Corrected v2 preflight

No API call was sent. No Batch was submitted.

## First Batch Failure

- Failed Batch ID: `{FAILED_BATCH_ID}`
- Successful requests: 0
- Failed requests: 2000
- Root cause: {ROOT_CAUSE}

## Metadata Correction

Only `body.metadata` values were changed. Boolean values are now strings (`true` / `false`), numeric values are stable strings, existing strings are unchanged, and `None` values are omitted.

- Previous materialized SHA-256: `{summary['previous_sha256']}`
- Corrected Batch: `{CORRECTED_BATCH}`
- Corrected SHA-256: `{summary['corrected_sha256']}`
- Metadata values converted: {summary['metadata_values_converted']}
- Metadata values checked: {summary['metadata_values_checked']}
- Non-string metadata remaining: {summary['non_string_metadata_remaining']}
- Prompts unchanged: {summary['prompts_unchanged']}
- Custom IDs unchanged: {summary['custom_ids_unchanged']}
- Locked scenarios unchanged: {summary['locked_scenarios_unchanged']}
- Locked run plan unchanged: {summary['locked_run_plan_unchanged']}

## Smoke Test File

- Smoke test file: `{SMOKE_BATCH}`
- Requests: {summary['smoke_requests']}
- Uses development data: {summary['smoke_uses_development_data']}
"""
    resubmission_protocol = f"""
# Corrected v2 resubmission protocol

This protocol is prepared for a later terminal run with `OPENAI_API_KEY` available. It is not executed by this preflight.

## Safety Gates

The script `src/resubmit_corrected_v2.py` performs local validation, verifies `OPENAI_API_KEY` without printing it, requires `CONFIRM_PAID_RUN=YES`, and requires the exact confirmation phrase:

`RUN 4 SMOKE TESTS THEN SUBMIT CORRECTED 2000 BATCH`

## Four Live Development Requests

The script first sends the four requests in `{SMOKE_BATCH}` with `client.responses.create(**body)`. The file uses a development scenario only, the same tool, the same schema, the same model `{MODEL}`, the endpoint `{ENDPOINT}`, and string-only metadata.

Smoke outputs will be written to `data/raw_api/smoke_test_corrected_v2_output.jsonl`.

If any smoke request fails, the script writes `reports/smoke_test_corrected_v2_failure.md` and stops before uploading the full Batch.

## Full Corrected Batch

Only after four valid smoke outputs, the script uploads `{CORRECTED_BATCH}` with `purpose=\"batch\"` and creates one Batch with `endpoint=\"/v1/responses\"`, `completion_window=\"24h\"`, and `experiment_id=\"confirmatory_2x2_corrected_v2\"`.

## Duplicate Protection

The corrected submission uses distinct state files:

- `batch/submissions/confirmatory_2x2_corrected_v2_state.json`
- `batch/submissions/confirmatory_2x2_corrected_v2_BATCH_ID.txt`

It blocks if the corrected v2 state already has a `batch_id`, if the same SHA-256 is recorded in `batch/submission_registry.json`, or if a corrected v2 submission is already in progress. The old failed Batch ID remains archived and does not block this new experiment ID and new SHA.
"""
    write_text("reports/metadata_type_fix_report.md", fix_report)
    write_text("reports/corrected_batch_validation_report.md", validation_report)
    write_text("reports/smoke_test_preflight.md", smoke_report)
    write_text("reports/corrected_v2_preflight.md", corrected_v2_preflight)
    write_text("reports/corrected_v2_resubmission_protocol.md", resubmission_protocol)


def main(emit: bool = True) -> dict[str, Any]:
    previous = read_jsonl(MATERIALIZED_BATCH)
    corrected = build_corrected_requests()
    corrected_from_locked_plan = build_corrected_requests_from_locked_plan()
    smoke = build_smoke_requests()
    write_jsonl(CORRECTED_BATCH, corrected)
    write_jsonl(SMOKE_BATCH, smoke)

    previous_normalized = [normalize_record_metadata(row) for row in previous]
    normalized_files_equivalent = previous_normalized == corrected
    locked_plan_builder_equivalent = corrected_from_locked_plan == corrected
    prompts_unchanged = [row.get("body", {}).get("input") for row in previous] == [row.get("body", {}).get("input") for row in corrected]
    custom_ids_unchanged = [row.get("custom_id") for row in previous] == [row.get("custom_id") for row in corrected]
    conversion = conversion_stats(previous)
    corrected_stats = metadata_stats(corrected)
    smoke_stats = metadata_stats(smoke)
    corrected_issues = validate_batch_shape(corrected, 2000)
    smoke_issues = validate_batch_shape(smoke, 4)
    conditions = Counter(row["custom_id"].split("__")[1] for row in corrected)
    condition_balance = all(conditions.get(condition, 0) == 500 for condition in CONDITIONS)
    smoke_custom_ids = [row.get("custom_id", "") for row in smoke]
    smoke_uses_development_data = all(cid.startswith("SMOKE_DEV_V2_") for cid in smoke_custom_ids) and not any("CON_" in json.dumps(row, ensure_ascii=False) for row in smoke)
    corrected_secret, corrected_real_action = contains_secret_or_real_action(CORRECTED_BATCH)
    smoke_secret, smoke_real_action = contains_secret_or_real_action(SMOKE_BATCH)
    locked_scenarios_hash = sha256_file(path("data/locked/confirmatory_scenarios.json"))
    locked_run_plan_hash = sha256_file(path("data/locked/confirmatory_run_plan.csv"))
    critical: list[str] = []
    critical.extend(corrected_issues)
    critical.extend(f"smoke: {issue}" for issue in smoke_issues)
    if not normalized_files_equivalent:
        critical.append("corrected Batch differs beyond metadata type normalization")
    if not locked_plan_builder_equivalent:
        critical.append("locked-plan builder output differs from normalized corrected Batch")
    if not prompts_unchanged:
        critical.append("prompts changed")
    if not custom_ids_unchanged:
        critical.append("custom IDs changed")
    if not condition_balance:
        critical.append(f"condition balance changed: {dict(conditions)}")
    if corrected_secret or smoke_secret:
        critical.append("API secret pattern detected")
    if corrected_real_action or smoke_real_action:
        critical.append("real action pattern detected")
    if locked_scenarios_hash != LOCKED_SCENARIOS_SHA256:
        critical.append("locked scenarios hash changed")
    if locked_run_plan_hash != LOCKED_RUN_PLAN_SHA256:
        critical.append("locked run plan hash changed")
    if not smoke_uses_development_data:
        critical.append("smoke test does not exclusively use development data")

    summary: dict[str, Any] = {
        "previous_sha256": sha256_file(path(MATERIALIZED_BATCH)),
        "corrected_sha256": sha256_file(path(CORRECTED_BATCH)),
        "corrected_requests": len(corrected),
        "unique_custom_ids": len({row.get("custom_id") for row in corrected}),
        "metadata_values_checked": corrected_stats["checked"],
        "non_string_metadata_remaining": corrected_stats["non_string"],
        "metadata_values_converted": conversion["converted"],
        "converted_fields": conversion["fields"],
        "metadata_fields": corrected_stats["fields"].keys(),
        "prompts_unchanged": "YES" if prompts_unchanged else "NO",
        "custom_ids_unchanged": "YES" if custom_ids_unchanged else "NO",
        "normalized_files_equivalent": "YES" if normalized_files_equivalent else "NO",
        "locked_scenarios_unchanged": "YES" if locked_scenarios_hash == LOCKED_SCENARIOS_SHA256 else "NO",
        "locked_run_plan_unchanged": "YES" if locked_run_plan_hash == LOCKED_RUN_PLAN_SHA256 else "NO",
        "smoke_requests": len(smoke),
        "smoke_unique_custom_ids": len(set(smoke_custom_ids)),
        "smoke_uses_development_data": "YES" if smoke_uses_development_data else "NO",
        "smoke_metadata_strings": "YES" if smoke_stats["non_string"] == 0 and not smoke_stats["issues"] else "NO",
        "smoke_secret_detected": smoke_secret,
        "smoke_real_action_detected": smoke_real_action,
        "critical_failures": len(critical),
        "critical": critical,
        "decision": "GO" if not critical else "NO-GO",
    }
    write_reports(summary)
    if emit:
        print(json.dumps({
            "decision": summary["decision"],
            "critical_failures": len(critical),
            "corrected_sha256": summary["corrected_sha256"],
            "smoke_requests": summary["smoke_requests"],
        }, indent=2))
    return summary


if __name__ == "__main__":
    main()
