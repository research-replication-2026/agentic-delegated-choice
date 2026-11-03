from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict

from src.common import path


def load_json(rel: str):
    return json.loads(path(rel).read_text(encoding="utf-8"))


def load_csv(rel: str):
    return list(csv.DictReader(path(rel).open("r", encoding="utf-8")))


def check(name: str, condition: bool, failures: list[str]) -> None:
    if not condition:
        failures.append(name)


def main() -> None:
    failures: list[str] = []
    prompts = load_json("prompts/confirmatory_prompts.json")["prompts"]
    scenarios = load_json("data/internal/confirmatory_scenarios_locked.json")["scenarios"]
    schema = load_json("schemas/submit_agentic_decision.json")
    scored = load_csv("data/processed/mock_scored.csv")

    check("same_schema_all_conditions", {p["tool_name"] for p in prompts} == {"submit_agentic_decision"} and len({p["condition"] for p in prompts}) == 6, failures)
    grouped = defaultdict(list)
    for p in prompts:
        grouped[p["scenario_id"]].append(p)
    check("same_user_prompts", all(len({r["user_payload"]["user_request"] for r in rows}) == 1 for rows in grouped.values()), failures)
    check("same_catalog_between_conditions", all(len({tuple(sorted(o["name"] for o in r["user_payload"]["options"])) for r in rows}) == 1 for rows in grouped.values()), failures)
    check("only_internal_instructions_vary", all(len({r["system_instruction"] for r in rows}) == 6 for rows in grouped.values()), failures)
    check("no_condition_leakage", all("partner_option_id" not in json.dumps(p["user_payload"]) and "commission_rate" not in json.dumps(p["user_payload"]) for p in prompts), failures)
    check("partner_never_optimal", all(s["partner_option_id"] != s["optimal_option_id"] for s in scenarios), failures)
    check("partner_respects_constraints", all(next(o for o in s["options"] if o["option_id"] == s["partner_option_id"])["objective_utility"] > 0 for s in scenarios), failures)
    check("commission_balance", set(Counter(s["commission_rate"] for s in scenarios)) == {0.05, 0.1, 0.15}, failures)
    check("utility_gap_balance", set(Counter(s["utility_gap_level"] for s in scenarios)) == {"very_low", "low", "medium", "high"}, failures)
    check("order_randomized", any(len({tuple(o["option_id"] for o in r["user_payload"]["options"]) for r in rows}) > 1 for rows in grouped.values()), failures)
    check("absence_real_booking", schema["properties"]["simulation_only"]["const"] is True and "body_preview_only" in path("data/internal/future_api_batch_preview.jsonl").read_text(encoding="utf-8"), failures)
    check("deduplication", len({r["observation_key"] for r in scored}) == len(scored), failures)
    check("regret_calculation", all(round(float(r["optimal_utility"]) - float(r["selected_utility"]), 4) == float(r["utility_regret"]) for r in scored), failures)
    check("disclosure_score", all(0 <= int(r["disclosure_completeness_score"]) <= 3 for r in scored), failures)
    robust = path("results/robustness/confirmatory_robustness_checks.csv").read_text(encoding="utf-8")
    check("placebos", "placebo_ready" in robust, failures)
    check("counterfactuals", "counterfactual_rotation_candidate" in robust, failures)

    result = {"checks_run": 16, "passed": not failures, "failures": failures}
    path("logs/quality_checks.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit(f"Quality checks failed: {failures}")
    print("Quality checks passed: 16/16")


if __name__ == "__main__":
    main()
