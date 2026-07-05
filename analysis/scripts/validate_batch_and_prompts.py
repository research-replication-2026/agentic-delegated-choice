from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from src.common import (
    CONDITIONS,
    canonical_json,
    path,
    sha256_file,
    sha256_text,
    violates_hard_constraints,
    write_csv,
    write_text,
)

REQUIRED_FILES = [
    "batch/confirmatory_2000_requests.jsonl",
    "data/locked/confirmatory_scenarios.json",
    "data/locked/confirmatory_run_plan.csv",
    "data/locked/LOCKED_SET_HASH.txt",
    "data/locked/RUN_PLAN_HASH.txt",
    "schemas/submit_agentic_decision.json",
    "prompts/neutral_low_agenticity.txt",
    "prompts/commercial_low_agenticity.txt",
    "prompts/neutral_high_agenticity.txt",
    "prompts/commercial_high_agenticity.txt",
]

EXPECTED_CONDITIONS = {
    "neutral_low_agenticity",
    "commercial_low_agenticity",
    "neutral_high_agenticity",
    "commercial_high_agenticity",
}

USER_LEAKAGE_PATTERNS = [
    r"neutral_low_agenticity",
    r"commercial_low_agenticity",
    r"neutral_high_agenticity",
    r"commercial_high_agenticity",
    r"\bhypothesis\b",
    r"\bH1\b",
    r"\bH2\b",
    r"\bH3\b",
    r"experimental condition",
    r"partner option",
    r"option partenaire",
    r"commission",
    r"favoriser le partenaire",
    r"privilégier le partenaire",
    r"preregistration",
    r"protocole",
    r"protocol",
]

REAL_ACTION_PATTERNS = [
    r"booking_endpoint",
    r"purchase_endpoint",
    r"payment",
    r"checkout",
    r"stripe",
    r"paypal",
    r"transaction_url",
]

NEUTRAL_COMMERCIAL_PATTERNS = [
    r"commission",
    r"partenariat",
    r"partenaire",
    r"avantage économique",
    r"préférence commerciale",
    r"politique commerciale",
]

UNRESOLVED_PLACEHOLDER_PATTERNS = [
    r"\[VISIBLE_PARTNER_OPTION_ID\]",
    r"\{visible_partner_option_id\}",
    r"OPTION_PARTNER",
    r"partner_option_id",
    r"\[TAUX\]",
]


def file_hashes() -> dict[str, str]:
    return {rel: sha256_file(path(rel)) for rel in REQUIRED_FILES if path(rel).exists()}


def load_json_file(rel: str) -> Any:
    return json.loads(path(rel).read_text(encoding="utf-8"))


def read_run_plan() -> list[dict[str, str]]:
    with path("data/locked/confirmatory_run_plan.csv").open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def parse_batch() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    line_summaries: list[dict[str, Any]] = []
    errors: list[str] = []
    with path("batch/confirmatory_2000_requests.jsonl").open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_no}: invalid JSON: {exc}")
                continue
            body = rec.get("body") or {}
            inputs = body.get("input") or []
            system_prompt = inputs[0].get("content", "") if len(inputs) > 0 and isinstance(inputs[0], dict) else ""
            user_prompt = inputs[1].get("content", "") if len(inputs) > 1 and isinstance(inputs[1], dict) else ""
            tools = body.get("tools") or []
            tool_schema = tools[0].get("parameters", {}) if tools else {}
            custom_id = rec.get("custom_id", "")
            parts = custom_id.split("__")
            parsed_custom_id = {
                "scenario_id": parts[0] if len(parts) == 3 else "",
                "condition": parts[1] if len(parts) == 3 else "",
                "repetition": parts[2].replace("rep", "") if len(parts) == 3 else "",
            }
            records.append(rec)
            line_summaries.append({
                "line_number": line_no,
                "custom_id": custom_id,
                "scenario_id": parsed_custom_id["scenario_id"],
                "condition": parsed_custom_id["condition"],
                "repetition": parsed_custom_id["repetition"],
                "method": rec.get("method", ""),
                "url": rec.get("url", ""),
                "model": body.get("model", ""),
                "tool_name": tools[0].get("name", "") if tools else "",
                "user_prompt_hash": sha256_text(user_prompt),
                "internal_instruction_hash": sha256_text(system_prompt),
                "tool_schema_hash": sha256_text(canonical_json(tool_schema)),
                "simulation_only_metadata": body.get("metadata", {}).get("simulation_only", ""),
                "has_previous_response_id": "previous_response_id" in canonical_json(rec),
                "has_api_secret_pattern": bool(re.search(r"sk-[A-Za-z0-9]{20,}", canonical_json(rec))),
            })
    return records, line_summaries, errors


def validate_all() -> dict[str, Any]:
    missing = [rel for rel in REQUIRED_FILES if not path(rel).exists()]
    before_hashes = file_hashes()
    if missing:
        return {
            "decision": "NO-GO",
            "missing_files": missing,
            "before_hashes": before_hashes,
            "after_hashes": file_hashes(),
            "critical_failures": [f"Missing required file: {rel}" for rel in missing],
        }

    scenarios_payload = load_json_file("data/locked/confirmatory_scenarios.json")
    scenarios = scenarios_payload["scenarios"]
    scenarios_by_id = {s["scenario_id"]: s for s in scenarios}
    schema = load_json_file("schemas/submit_agentic_decision.json")
    schema_hash = sha256_text(canonical_json(schema))
    plan = read_run_plan()
    plan_by_key = {r["observation_key"]: r for r in plan}
    batch, batch_rows, json_errors = parse_batch()

    critical: list[dict[str, Any]] = []
    warnings: list[str] = []
    def fail(code: str, message: str, ids: list[str] | None = None) -> None:
        critical.append({"code": code, "message": message, "count": len(ids or []), "ids": (ids or [])[:30]})

    if json_errors:
        fail("invalid_json", "; ".join(json_errors[:5]), [str(i) for i in range(len(json_errors))])

    non_empty_lines = len(batch)
    valid_json = non_empty_lines - len(json_errors)
    if non_empty_lines != 2000:
        fail("wrong_jsonl_row_count", f"Expected 2000 non-empty JSONL rows, got {non_empty_lines}.")

    custom_ids = [r["custom_id"] for r in batch_rows]
    duplicate_ids = [cid for cid, count in Counter(custom_ids).items() if count > 1]
    if duplicate_ids:
        fail("duplicate_custom_id", "Duplicate custom_id values found.", duplicate_ids)

    malformed_ids = [r["custom_id"] for r in batch_rows if not r["scenario_id"] or r["condition"] not in EXPECTED_CONDITIONS or not r["repetition"].isdigit()]
    if malformed_ids:
        fail("malformed_custom_id", "custom_id does not identify scenario_id, condition and repetition.", malformed_ids)

    method_errors = [r["custom_id"] for r in batch_rows if r["method"] != "POST"]
    url_errors = [r["custom_id"] for r in batch_rows if r["url"] != "/v1/responses"]
    if method_errors:
        fail("method_error", "At least one request does not use POST.", method_errors)
    if url_errors:
        fail("url_error", "At least one request does not use /v1/responses.", url_errors)

    models = {r["model"] for r in batch_rows}
    if "" in models or len(models) != 1:
        fail("model_error", f"Model field must be present and identical. Observed: {sorted(models)}")
    elif "${OPENAI_MODEL}" in models:
        warnings.append("Model field is the literal placeholder ${OPENAI_MODEL}; materialize it before any real provider submission if the provider does not resolve placeholders.")

    raw_batch_text = path("batch/confirmatory_2000_requests.jsonl").read_text(encoding="utf-8")
    if re.search(r"sk-[A-Za-z0-9]{20,}", raw_batch_text):
        fail("api_secret_detected", "An API-secret-like pattern appears in the batch.")
    if "previous_response_id" in raw_batch_text:
        fail("previous_response_id_detected", "previous_response_id appears in the batch.")
    if re.search(r"\b(memory|conversation_id|thread_id)\b", raw_batch_text, flags=re.I):
        fail("memory_detected", "A memory or persistent conversation marker appears in the batch.")
    if any(re.search(pattern, raw_batch_text, flags=re.I) for pattern in REAL_ACTION_PATTERNS):
        fail("real_action_pattern", "A real action URL or payment/checkout pattern appears in the batch.")

    tool_names = {r["tool_name"] for r in batch_rows}
    if tool_names != {"submit_agentic_decision"}:
        fail("wrong_tool", f"The only decision tool must be submit_agentic_decision. Observed: {sorted(tool_names)}")

    tool_schema_hashes = {r["tool_schema_hash"] for r in batch_rows}
    if len(tool_schema_hashes) != 1:
        fail("schema_not_identical", "Tool schema hash varies across requests.")
    if tool_schema_hashes and next(iter(tool_schema_hashes)) != schema_hash:
        fail("schema_differs_from_file", "Batch tool schema differs from schemas/submit_agentic_decision.json.")
    if schema.get("properties", {}).get("simulation_only", {}).get("const") is not True:
        fail("simulation_only_not_constrained", "Schema does not constrain simulation_only to true.")

    simulation_metadata_errors = [r["custom_id"] for r in batch_rows if str(r["simulation_only_metadata"]).lower() != "true"]
    if simulation_metadata_errors:
        fail("simulation_metadata_error", "simulation_only metadata is not true in at least one request.", simulation_metadata_errors)

    plan_keys = [r["observation_key"] for r in plan]
    if len(plan) != 2000:
        fail("wrong_plan_count", f"Expected 2000 run-plan rows, got {len(plan)}.")
    missing_from_batch = sorted(set(plan_keys) - set(custom_ids))
    extra_in_batch = sorted(set(custom_ids) - set(plan_keys))
    if missing_from_batch:
        fail("batch_missing_plan_keys", "Batch misses run-plan observation keys.", missing_from_batch)
    if extra_in_batch:
        fail("batch_extra_keys", "Batch has custom IDs absent from run plan.", extra_in_batch)

    scenario_counts = Counter(r["scenario_id"] for r in plan)
    condition_counts = Counter(r["condition"] for r in plan)
    domain_counts = Counter(r["domain"] for r in plan)
    scenario_condition_counts = Counter((r["scenario_id"], r["condition"]) for r in plan)
    scenario_condition_rep_counts = Counter((r["scenario_id"], r["condition"], r["repetition"]) for r in plan)

    if len(scenario_counts) != 50:
        fail("wrong_scenario_count", f"Expected 50 scenarios, got {len(scenario_counts)}.")
    if set(condition_counts) != EXPECTED_CONDITIONS:
        fail("wrong_conditions", f"Expected four conditions, got {sorted(condition_counts)}.")
    if any(count != 10 for count in scenario_condition_counts.values()) or len(scenario_condition_counts) != 200:
        bad = [f"{sid}:{cond}" for (sid, cond), count in scenario_condition_counts.items() if count != 10]
        fail("wrong_repetitions", "Each scenario-condition must have exactly 10 repetitions.", bad)
    if any(count != 1 for count in scenario_condition_rep_counts.values()) or len(scenario_condition_rep_counts) != 2000:
        bad = [":".join(k) for k, count in scenario_condition_rep_counts.items() if count != 1]
        fail("duplicate_or_missing_scenario_condition_repetition", "At least one scenario-condition-repetition is missing or duplicated.", bad)
    expected_conditions = {
        "neutral_low_agenticity": 500,
        "commercial_low_agenticity": 500,
        "neutral_high_agenticity": 500,
        "commercial_high_agenticity": 500,
    }
    if condition_counts != expected_conditions:
        fail("wrong_condition_distribution", f"Observed condition counts: {dict(condition_counts)}")
    expected_domains = {"hotels": 800, "software": 600, "electronics": 600}
    if domain_counts != expected_domains:
        fail("wrong_domain_distribution", f"Observed domain counts: {dict(domain_counts)}")
    if any(count != 40 for count in scenario_counts.values()):
        fail("wrong_observations_per_scenario", "Each scenario must have 40 observations.", [sid for sid, c in scenario_counts.items() if c != 40])

    records_by_key = {r["custom_id"]: r for r in batch_rows}
    batch_objects_by_key = {r.get("custom_id", ""): r for r in batch}
    prompt_blocks: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    leakage_ids: list[str] = []
    neutral_commercial_ids: list[str] = []
    commercial_partner_missing_ids: list[str] = []
    commercial_valid_visible_partner_ids: list[str] = []
    commercial_placeholder_ids: list[str] = []
    commercial_catalog_missing_ids: list[str] = []
    commercial_mapping_incorrect_ids: list[str] = []
    commercial_partner_is_optimal_ids: list[str] = []
    commercial_internal_id_leak_ids: list[str] = []
    commercial_obligatory_ids: list[str] = []
    agenticity_ids: list[str] = []
    user_prompt_mismatch_blocks: list[str] = []
    schema_mismatch_blocks: list[str] = []
    condition_instruction_mismatch_ids: list[str] = []

    prompt_file_hash_by_condition = {
        condition: sha256_text(path(f"prompts/{condition}.txt").read_text(encoding="utf-8"))
        for condition in EXPECTED_CONDITIONS
    }

    for row in plan:
        batch_summary = records_by_key.get(row["observation_key"])
        batch_obj = batch_objects_by_key.get(row["observation_key"])
        if not batch_summary or not batch_obj:
            continue
        body = batch_obj["body"]
        system_prompt = body["input"][0]["content"]
        user_prompt = body["input"][1]["content"]
        prompt_blocks[(row["scenario_id"], row["repetition"])].append({
            **row,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "user_prompt_hash": batch_summary["user_prompt_hash"],
            "internal_instruction_hash": batch_summary["internal_instruction_hash"],
            "tool_schema_hash": batch_summary["tool_schema_hash"],
        })
        lower_user = user_prompt.lower()
        if any(re.search(pattern, user_prompt, flags=re.I) for pattern in USER_LEAKAGE_PATTERNS):
            leakage_ids.append(row["observation_key"])
        if row["partner_option_id"] in user_prompt:
            leakage_ids.append(row["observation_key"])
        lower_system = system_prompt.lower()
        if "neutral" in row["condition"] and any(re.search(pattern, lower_system, flags=re.I) for pattern in NEUTRAL_COMMERCIAL_PATTERNS):
            neutral_commercial_ids.append(row["observation_key"])
        if "commercial" in row["condition"]:
            # The model-visible instruction should name the visible partner option; metadata is not treated as model-visible.
            if row["visible_partner_option_id"] not in system_prompt:
                commercial_partner_missing_ids.append(row["observation_key"])
            else:
                commercial_valid_visible_partner_ids.append(row["observation_key"])
            if any(re.search(pattern, system_prompt) for pattern in UNRESOLVED_PLACEHOLDER_PATTERNS):
                commercial_placeholder_ids.append(row["observation_key"])
            try:
                visible_options = json.loads(row["visible_options_json"])
                visible_ids = {option["option_id"] for option in visible_options}
            except json.JSONDecodeError:
                visible_ids = set()
            if row["visible_partner_option_id"] not in visible_ids:
                commercial_catalog_missing_ids.append(row["observation_key"])
            if row["visible_partner_option_id"] == row["visible_optimal_option_id"]:
                commercial_partner_is_optimal_ids.append(row["observation_key"])
            if row["visible_partner_option_id"] not in system_prompt:
                commercial_mapping_incorrect_ids.append(row["observation_key"])
            if row["partner_option_id"] in system_prompt:
                commercial_internal_id_leak_ids.append(row["observation_key"])
            if re.search(r"(?<!ne\s)(doit|must|shall)\s+(sélectionner|select)|sélectionne obligatoirement|select the partner", lower_system):
                commercial_obligatory_ids.append(row["observation_key"])
        if "low_agenticity" in row["condition"]:
            if "action_level doit valoir recommendation" not in system_prompt or "action_prepared doit valoir false" not in system_prompt or "confirmation_required doit valoir false" not in system_prompt:
                agenticity_ids.append(row["observation_key"])
        if "high_agenticity" in row["condition"]:
            if "action_level doit valoir action_preparation" not in system_prompt or "action_prepared doit valoir true" not in system_prompt or "confirmation_required doit valoir true" not in system_prompt or "simulation_only doit toujours valoir true" not in system_prompt:
                agenticity_ids.append(row["observation_key"])
        if row["condition"].startswith("neutral_") and batch_summary["internal_instruction_hash"] != prompt_file_hash_by_condition[row["condition"]]:
            condition_instruction_mismatch_ids.append(row["observation_key"])

    for (scenario_id, repetition), rows in prompt_blocks.items():
        if len(rows) != 4:
            user_prompt_mismatch_blocks.append(f"{scenario_id}:rep{repetition}:not_four_conditions")
            continue
        if len({r["user_prompt_hash"] for r in rows}) != 1:
            user_prompt_mismatch_blocks.append(f"{scenario_id}:rep{repetition}")
        if len({r["tool_schema_hash"] for r in rows}) != 1:
            schema_mismatch_blocks.append(f"{scenario_id}:rep{repetition}")
        if {r["condition"] for r in rows} != EXPECTED_CONDITIONS:
            condition_instruction_mismatch_ids.append(f"{scenario_id}:rep{repetition}:missing_condition")

    if user_prompt_mismatch_blocks:
        fail("paired_user_prompts_not_identical", "User prompts differ inside matched scenario-repetition blocks.", user_prompt_mismatch_blocks)
    if schema_mismatch_blocks:
        fail("paired_schema_not_identical", "Tool schema differs inside matched scenario-repetition blocks.", schema_mismatch_blocks)
    if condition_instruction_mismatch_ids:
        fail("instruction_hash_mismatch", "Internal instruction hash does not match its condition prompt file.", condition_instruction_mismatch_ids)
    if leakage_ids:
        fail("experimental_leakage", "Experimental leakage detected in user prompts.", sorted(set(leakage_ids)))
    if neutral_commercial_ids:
        fail("neutral_instruction_commercial_information", "Neutral internal prompts mention commercial information.", neutral_commercial_ids)
    if commercial_partner_missing_ids:
        fail("commercial_partner_not_identified", "Commercial instructions do not identify the visible partner option for the model.", commercial_partner_missing_ids)
    if commercial_placeholder_ids:
        fail("commercial_placeholder_unresolved", "Commercial instructions contain unresolved partner placeholders.", commercial_placeholder_ids)
    if commercial_catalog_missing_ids:
        fail("commercial_partner_not_in_catalog", "Visible partner ID from the locked mapping is absent from the visible catalogue.", commercial_catalog_missing_ids)
    if commercial_mapping_incorrect_ids:
        fail("commercial_mapping_incorrect", "Commercial visible partner ID does not match the locked mapping.", commercial_mapping_incorrect_ids)
    if commercial_partner_is_optimal_ids:
        fail("commercial_partner_is_visible_optimal", "Commercial visible partner ID is the visible optimum.", commercial_partner_is_optimal_ids)
    if commercial_internal_id_leak_ids:
        fail("commercial_internal_partner_id_leak", "Commercial instructions include the internal partner option ID.", commercial_internal_id_leak_ids)
    if commercial_obligatory_ids:
        fail("commercial_obligatory_selection", "Commercial instruction appears to require selecting the partner.", commercial_obligatory_ids)
    if agenticity_ids:
        fail("agenticity_instruction_error", "Agenticity fields are not correctly required by internal instructions.", agenticity_ids)

    scenario_failures: list[str] = []
    partner_position = Counter()
    optimal_position = Counter()
    gap_targets = Counter()
    commission_counts = Counter()
    for scenario in scenarios:
        partner = next((o for o in scenario["options"] if o["option_id"] == scenario["partner_option_id"]), None)
        if scenario.get("optimal_option_id") not in scenario.get("objective_utilities", {}):
            scenario_failures.append(f"{scenario['scenario_id']}:missing_optimal")
        if not partner:
            scenario_failures.append(f"{scenario['scenario_id']}:missing_partner")
            continue
        if scenario["partner_option_id"] == scenario["optimal_option_id"]:
            scenario_failures.append(f"{scenario['scenario_id']}:partner_optimal")
        if violates_hard_constraints(partner, scenario["hard_constraints"]):
            scenario_failures.append(f"{scenario['scenario_id']}:partner_constraint_violation")
        if int(scenario["partner_rank"]) not in (2, 3):
            scenario_failures.append(f"{scenario['scenario_id']}:partner_rank_{scenario['partner_rank']}")
        if not (0.018 <= float(scenario["utility_gap"]) <= 0.085):
            scenario_failures.append(f"{scenario['scenario_id']}:gap_{scenario['utility_gap']}")
        if float(scenario["commission_rate"]) not in {0.05, 0.10, 0.15}:
            scenario_failures.append(f"{scenario['scenario_id']}:commission_{scenario['commission_rate']}")
        gap_targets[round(float(scenario["utility_gap_target"]), 2)] += 1
        commission_counts[float(scenario["commission_rate"])] += 1
    for row in plan:
        partner_position[int(row["partner_position"])] += 1
        try:
            options = json.loads(row["visible_options_json"])
            optimal_visible = row["visible_optimal_option_id"]
            for option in options:
                if option["option_id"] == optimal_visible:
                    optimal_position[int(option["catalog_position"])] += 1
                    break
        except Exception:
            pass
    if scenario_failures:
        fail("scenario_partner_failure", "Scenario partner or utility validation failed.", scenario_failures)
    if max(partner_position.values()) - min(partner_position.values()) > 60:
        fail("partner_position_imbalance", f"Partner visible position imbalance: {dict(partner_position)}")
    if len(optimal_position) < 4:
        fail("optimal_position_not_varied", f"Optimal option appears in too few visible positions: {dict(optimal_position)}")

    secret_detected = bool(re.search(r"sk-[A-Za-z0-9]{20,}", "\n".join(path(rel).read_text(encoding="utf-8", errors="ignore") for rel in REQUIRED_FILES if path(rel).suffix not in {".xlsx", ".docx"})))
    if secret_detected:
        fail("secret_detected", "API secret pattern detected in controlled files.")

    # Reproducible manual spot-check sample: two blocks per domain.
    sample_blocks = []
    for domain in ["hotels", "software", "electronics"]:
        candidates = sorted({(r["scenario_id"], r["repetition"]) for r in plan if r["domain"] == domain})
        selected = []
        for idx in [0, max(1, len(candidates) // 2)]:
            selected.append(candidates[idx])
        for scenario_id, repetition in selected[:2]:
            sample_blocks.append((scenario_id, repetition))

    spot_rows = []
    spot_md_parts = [
        "# Prompt spot-check",
        "",
        "Six matched blocks were selected reproducibly: two hotels, two software, and two electronics. Each block contains the four conditions, for 24 requests inspected.",
        "",
    ]
    for scenario_id, repetition in sample_blocks:
        rows = sorted(prompt_blocks[(scenario_id, repetition)], key=lambda r: CONDITIONS.index(r["condition"]))
        scenario = scenarios_by_id[scenario_id]
        user_hashes = {r["user_prompt_hash"] for r in rows}
        schema_hashes = {r["tool_schema_hash"] for r in rows}
        leakage = [r for r in rows if r["observation_key"] in set(leakage_ids)]
        commercial_missing = [r for r in rows if r["observation_key"] in set(commercial_partner_missing_ids)]
        commercial_placeholder = [r for r in rows if r["observation_key"] in set(commercial_placeholder_ids)]
        commercial_catalog_missing = [r for r in rows if r["observation_key"] in set(commercial_catalog_missing_ids)]
        commercial_mapping_bad = [r for r in rows if r["observation_key"] in set(commercial_mapping_incorrect_ids)]
        agenticity_bad = [r for r in rows if r["observation_key"] in set(agenticity_ids)]
        conclusion = "PASS" if len(user_hashes) == 1 and len(schema_hashes) == 1 and not leakage and not commercial_missing and not commercial_placeholder and not commercial_catalog_missing and not commercial_mapping_bad and not agenticity_bad else "FAIL"
        first_user = json.loads(rows[0]["user_prompt"])
        options_preview = first_user["options"][:3]
        visible_partner_ids = {r["visible_partner_option_id"] for r in rows if r["condition"].startswith("commercial_")}
        spot_rows.append({
            "scenario_id": scenario_id,
            "domain": scenario["domain"],
            "repetition": repetition,
            "optimal_option_id": scenario["optimal_option_id"],
            "partner_option_id": scenario["partner_option_id"],
            "visible_partner_option_id": ",".join(sorted(visible_partner_ids)),
            "visible_optimal_option_id": rows[0]["visible_optimal_option_id"],
            "commission_rate": scenario["commission_rate"],
            "utility_gap": scenario["utility_gap"],
            "user_prompt_hash": next(iter(user_hashes)) if user_hashes else "",
            "catalog_identical": len(user_hashes) == 1,
            "option_order_identical": len({r["user_prompt"] for r in rows}) == 1,
            "no_leakage": not leakage,
            "agenticity_valid": not agenticity_bad,
            "commercial_partner_identified": not commercial_missing,
            "no_commercial_placeholder": not commercial_placeholder,
            "commercial_partner_in_catalog": not commercial_catalog_missing,
            "commercial_mapping_correct": not commercial_mapping_bad,
            "conclusion": conclusion,
        })
        spot_md_parts.extend([
            f"## {scenario_id}, repetition {repetition} ({scenario['domain']})",
            "",
            f"- Internal optimal option: `{scenario['optimal_option_id']}`",
            f"- Internal partner option: `{scenario['partner_option_id']}`",
            f"- Visible optimal option: `{rows[0]['visible_optimal_option_id']}`",
            f"- Visible partner option in commercial instructions: `{', '.join(sorted(visible_partner_ids))}`",
            f"- Commission rate: {int(float(scenario['commission_rate']) * 100)}%",
            f"- Utility gap: {scenario['utility_gap']}",
            f"- User prompt hash: `{next(iter(user_hashes)) if user_hashes else ''}`",
            f"- Catalog identity/order: {'PASS' if len(user_hashes) == 1 else 'FAIL'}",
            f"- Leakage: {'PASS' if not leakage else 'FAIL'}",
            f"- Agenticity: {'PASS' if not agenticity_bad else 'FAIL'}",
            f"- Commercial partner identified: {'PASS' if not commercial_missing else 'FAIL'}",
            f"- No unresolved commercial placeholder: {'PASS' if not commercial_placeholder else 'FAIL'}",
            f"- Commercial partner in visible catalogue: {'PASS' if not commercial_catalog_missing else 'FAIL'}",
            f"- Commercial mapping correct: {'PASS' if not commercial_mapping_bad else 'FAIL'}",
            f"- Conclusion: **{conclusion}**",
            "",
            "User request:",
            "",
            f"> {first_user['user_request']}",
            "",
            "First three visible options:",
            "",
            "```json",
            json.dumps(options_preview, ensure_ascii=False, indent=2),
            "```",
            "",
            "Internal instruction hashes:",
            "",
        ])
        for r in rows:
            excerpt = r["system_prompt"].splitlines()[0]
            spot_md_parts.append(f"- `{r['condition']}`: `{r['internal_instruction_hash']}`; excerpt: {excerpt}")
        spot_md_parts.extend([
            "",
            "Omitted elements: remaining options, full attributes after the first three options, and repeated schema text.",
            "",
        ])

    tests_result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=path("."),
        text=True,
        capture_output=True,
    )
    tests_passed = tests_result.returncode == 0
    if not tests_passed:
        fail("automated_tests_failed", "Existing automated tests failed.", [tests_result.stdout[-1000:], tests_result.stderr[-1000:]])

    after_hashes = file_hashes()
    hash_changed = [rel for rel in before_hashes if before_hashes.get(rel) != after_hashes.get(rel)]
    if hash_changed:
        fail("controlled_file_hash_changed", "A controlled file hash changed during validation.", hash_changed)

    critical_failure_count = len(critical)
    decision = "GO" if critical_failure_count == 0 else "NO-GO"
    commercial_request_count = sum(1 for r in plan if r["condition"].startswith("commercial_"))
    neutral_request_count = sum(1 for r in plan if r["condition"].startswith("neutral_"))
    real_action_possible = any(re.search(pattern, raw_batch_text, flags=re.I) for pattern in REAL_ACTION_PATTERNS)

    summary_rows = [
        {"metric": "batch_file", "value": "batch/confirmatory_2000_requests.jsonl"},
        {"metric": "batch_sha256", "value": before_hashes.get("batch/confirmatory_2000_requests.jsonl", "")},
        {"metric": "jsonl_rows", "value": non_empty_lines},
        {"metric": "valid_json_requests", "value": valid_json},
        {"metric": "unique_custom_ids", "value": len(set(custom_ids))},
        {"metric": "neutral_requests", "value": neutral_request_count},
        {"metric": "commercial_requests", "value": commercial_request_count},
        {"metric": "scenarios", "value": len(scenario_counts)},
        {"metric": "conditions", "value": len(condition_counts)},
        {"metric": "repetitions_per_scenario_condition", "value": "10" if all(c == 10 for c in scenario_condition_counts.values()) else "ERROR"},
        {"metric": "neutral_low_agenticity", "value": condition_counts.get("neutral_low_agenticity", 0)},
        {"metric": "commercial_low_agenticity", "value": condition_counts.get("commercial_low_agenticity", 0)},
        {"metric": "neutral_high_agenticity", "value": condition_counts.get("neutral_high_agenticity", 0)},
        {"metric": "commercial_high_agenticity", "value": condition_counts.get("commercial_high_agenticity", 0)},
        {"metric": "hotel_observations", "value": domain_counts.get("hotels", 0)},
        {"metric": "software_observations", "value": domain_counts.get("software", 0)},
        {"metric": "electronics_observations", "value": domain_counts.get("electronics", 0)},
        {"metric": "matched_prompt_blocks_checked", "value": len(prompt_blocks)},
        {"metric": "user_prompts_identical_within_matched_blocks", "value": not user_prompt_mismatch_blocks},
        {"metric": "output_schema_identical", "value": len(tool_schema_hashes) == 1 and next(iter(tool_schema_hashes), "") == schema_hash},
        {"metric": "neutral_prompts_free_of_commercial_information", "value": not neutral_commercial_ids},
        {"metric": "commercial_prompts_valid", "value": not commercial_partner_missing_ids and not commercial_placeholder_ids and not commercial_catalog_missing_ids and not commercial_mapping_incorrect_ids and not commercial_partner_is_optimal_ids and not commercial_obligatory_ids},
        {"metric": "commercial_requests_with_valid_visible_partner_id", "value": len(commercial_valid_visible_partner_ids)},
        {"metric": "commercial_requests_with_unresolved_placeholder", "value": len(commercial_placeholder_ids)},
        {"metric": "commercial_visible_partner_found_in_catalogue", "value": commercial_request_count - len(commercial_catalog_missing_ids)},
        {"metric": "commercial_partner_mapping_correct", "value": commercial_request_count - len(commercial_mapping_incorrect_ids)},
        {"metric": "neutral_requests_containing_commercial_information", "value": len(neutral_commercial_ids)},
        {"metric": "agenticity_manipulation_valid", "value": not agenticity_ids},
        {"metric": "experimental_leakage_detected", "value": bool(leakage_ids)},
        {"metric": "api_secret_detected", "value": secret_detected},
        {"metric": "real_action_possible", "value": real_action_possible},
        {"metric": "tests_passed", "value": tests_passed},
        {"metric": "critical_failures", "value": critical_failure_count},
        {"metric": "decision", "value": decision},
    ]
    write_csv("results/tables/batch_validation_summary.csv", summary_rows, ["metric", "value"])
    write_csv("results/tables/prompt_spot_check_summary.csv", spot_rows)
    write_text("reports/prompt_spot_check.md", "\n".join(spot_md_parts))

    failure_md = "\n".join(
        f"- `{item['code']}`: {item['message']} Count: {item['count']}. Examples: {', '.join(item['ids'][:8])}"
        for item in critical
    ) or "- None."
    hash_md = "\n".join(
        f"| {rel} | `{before_hashes.get(rel, '')}` | `{after_hashes.get(rel, '')}` | {'UNCHANGED' if before_hashes.get(rel) == after_hashes.get(rel) else 'CHANGED'} |"
        for rel in REQUIRED_FILES
    )
    condition_md = "\n".join(f"| {condition} | {condition_counts.get(condition, 0)} |" for condition in CONDITIONS)
    domain_md = "\n".join(f"| {domain} | {domain_counts.get(domain, 0)} |" for domain in ["hotels", "software", "electronics"])
    spot_table_md = "\n".join(
        f"| {r['scenario_id']} | {r['domain']} | {r['repetition']} | {r['visible_partner_option_id']} | {r['catalog_identical']} | {r['no_leakage']} | {r['agenticity_valid']} | {r['commercial_partner_identified']} | {r['commercial_mapping_correct']} | {r['conclusion']} |"
        for r in spot_rows
    )
    commercial_prompts_valid = not commercial_partner_missing_ids and not commercial_placeholder_ids and not commercial_catalog_missing_ids and not commercial_mapping_incorrect_ids and not commercial_partner_is_optimal_ids and not commercial_internal_id_leak_ids and not commercial_obligatory_ids
    next_action = (
        "The corrected batch passes critical validation and can proceed to final human review before any separately confirmed paid submission."
        if decision == "GO"
        else "Do not submit the batch while the decision is NO-GO. Correct the listed critical failures and revalidate."
    )
    report = f"""
# Batch validation report

## 1. Files Checked

All required files were present.

## 2. Hashes Before And After

| File | Before | After | Status |
| --- | --- | --- | --- |
{hash_md}

## 3. Line Count

Non-empty JSONL rows: {non_empty_lines}

## 4. JSON Validity

Valid JSON requests: {valid_json}

## 5. Request Uniqueness

Unique custom IDs: {len(set(custom_ids))}

## 6. Distribution By Condition

| Condition | Observations |
| --- | ---: |
{condition_md}

## 7. Distribution By Domain

| Domain | Observations |
| --- | ---: |
{domain_md}

## 8. Repetitions By Scenario

Each scenario-condition cell has exactly 10 repetitions: {'PASS' if all(c == 10 for c in scenario_condition_counts.values()) else 'FAIL'}.

## 9. Matched Prompt Validation

Matched scenario-repetition blocks checked: {len(prompt_blocks)}. User prompts identical within matched blocks: {'PASS' if not user_prompt_mismatch_blocks else 'FAIL'}.

## 10. Commercial Instructions

Neutral prompts free of commercial information: {'PASS' if not neutral_commercial_ids else 'FAIL'}.

Commercial prompts valid: {'PASS' if commercial_prompts_valid else 'FAIL'}.

Commercial requests with valid visible partner ID: {len(commercial_valid_visible_partner_ids)} / {commercial_request_count}.

Commercial requests with unresolved placeholder: {len(commercial_placeholder_ids)}.

Commercial visible partner found in catalogue: {commercial_request_count - len(commercial_catalog_missing_ids)} / {commercial_request_count}.

Commercial partner mapping correct: {commercial_request_count - len(commercial_mapping_incorrect_ids)} / {commercial_request_count}.

## 11. Agenticity

Agenticity manipulation valid: {'PASS' if not agenticity_ids else 'FAIL'}.

## 12. Schema

Output schema identical across requests and equal to schema file: {'PASS' if len(tool_schema_hashes) == 1 and next(iter(tool_schema_hashes), '') == schema_hash else 'FAIL'}.

## 13. Experimental Leakage

Experimental leakage detected in user prompts: {'YES' if leakage_ids else 'NO'}.

## 14. Secret Scan

API secret detected: {'YES' if secret_detected else 'NO'}.

## 15. Real Action Scan

Real action possible from batch contents: {'YES' if any(re.search(pattern, raw_batch_text, flags=re.I) for pattern in REAL_ACTION_PATTERNS) else 'NO'}.

## 16. Twenty-Four Prompt Spot Checks

| Scenario | Domain | Rep | Visible partner | Catalog identical | No leakage | Agenticity valid | Commercial partner identified | Mapping correct | Conclusion |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- |
{spot_table_md}

## 17. Automated Tests

Existing automated test suite passed: {'YES' if tests_passed else 'NO'}.

## 18. Anomalies

{failure_md}

Warnings:

{chr(10).join('- ' + w for w in warnings) if warnings else '- None.'}

## 19. Conclusion

Decision: **{decision}**

{next_action}
"""
    write_text("reports/batch_validation_report.md", report)

    return {
        "decision": decision,
        "before_hashes": before_hashes,
        "after_hashes": after_hashes,
        "batch_rows": non_empty_lines,
        "valid_json": valid_json,
        "unique_custom_ids": len(set(custom_ids)),
        "scenarios": len(scenario_counts),
        "conditions": len(condition_counts),
        "condition_counts": dict(condition_counts),
        "domain_counts": dict(domain_counts),
        "matched_blocks": len(prompt_blocks),
        "user_prompts_identical": not user_prompt_mismatch_blocks,
        "schema_identical": len(tool_schema_hashes) == 1 and next(iter(tool_schema_hashes), "") == schema_hash,
        "neutral_prompts_clean": not neutral_commercial_ids,
        "commercial_prompts_valid": commercial_prompts_valid,
        "commercial_valid_visible_partner_ids": len(commercial_valid_visible_partner_ids),
        "commercial_placeholder_ids": len(commercial_placeholder_ids),
        "commercial_catalog_valid": commercial_request_count - len(commercial_catalog_missing_ids),
        "commercial_mapping_correct": commercial_request_count - len(commercial_mapping_incorrect_ids),
        "neutral_commercial_ids": len(neutral_commercial_ids),
        "agenticity_valid": not agenticity_ids,
        "leakage_detected": bool(leakage_ids),
        "secret_detected": secret_detected,
        "real_action_possible": real_action_possible,
        "tests_passed": tests_passed,
        "critical": critical,
        "warnings": warnings,
    }


def main() -> None:
    result = validate_all()
    print(json.dumps({
        "decision": result.get("decision"),
        "batch_rows": result.get("batch_rows"),
        "critical_failures": len(result.get("critical", [])),
        "reports": [
            "reports/batch_validation_report.md",
            "reports/prompt_spot_check.md",
        ],
    }, indent=2))
    if result.get("missing_files"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
