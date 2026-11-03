from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def test_same_output_schema_in_all_conditions() -> None:
    prompts = load("prompts/confirmatory_prompts.json")["prompts"]
    assert {p["tool_name"] for p in prompts} == {"submit_agentic_decision"}
    schema = load("schemas/submit_agentic_decision.json")
    assert "action_level" in schema["properties"]
    assert len({p["condition"] for p in prompts}) == 6


def test_same_catalogs_and_user_prompts_between_conditions() -> None:
    grouped = defaultdict(list)
    for p in load("prompts/confirmatory_prompts.json")["prompts"]:
        grouped[p["scenario_id"]].append(p)
    for rows in grouped.values():
        assert len({r["user_payload"]["user_request"] for r in rows}) == 1
        assert len({tuple(sorted(o["name"] for o in r["user_payload"]["options"])) for r in rows}) == 1


def test_only_internal_instructions_vary() -> None:
    rows = load("prompts/confirmatory_prompts.json")["prompts"]
    by_scenario = defaultdict(list)
    for r in rows:
        by_scenario[r["scenario_id"]].append(r)
    for scenario_rows in by_scenario.values():
        user_payloads = {json.dumps(r["user_payload"], sort_keys=True) for r in scenario_rows}
        assert len(user_payloads) == 6  # option order is independently randomized
        assert len({r["system_instruction"] for r in scenario_rows}) == 6


def test_no_condition_leakage_in_user_payload() -> None:
    for p in load("prompts/confirmatory_prompts.json")["prompts"]:
        text = json.dumps(p["user_payload"])
        assert "partner_option_id" not in text
        assert "commission_rate" not in text
        assert "C2" not in text


def test_partner_never_optimal_and_respects_constraints() -> None:
    scenarios = load("data/internal/confirmatory_scenarios_locked.json")["scenarios"]
    for s in scenarios:
        assert s["partner_option_id"] != s["optimal_option_id"]
        assert s["partner_rank"] in (2, 3)
        partner = next(o for o in s["options"] if o["option_id"] == s["partner_option_id"])
        assert partner["objective_utility"] > 0


def test_commission_and_gap_balance() -> None:
    scenarios = load("data/internal/confirmatory_scenarios_locked.json")["scenarios"]
    assert len(scenarios) == 60
    assert Counter(s["domain"] for s in scenarios) == {"hotels": 20, "software": 20, "electronics": 20}
    assert set(Counter(s["commission_rate"] for s in scenarios)) == {0.05, 0.1, 0.15}
    assert set(Counter(s["utility_gap_level"] for s in scenarios)) == {"very_low", "low", "medium", "high"}


def test_order_randomized() -> None:
    prompts = load("prompts/confirmatory_prompts.json")["prompts"]
    by_scenario = defaultdict(list)
    for p in prompts:
        by_scenario[p["scenario_id"]].append(tuple(o["option_id"] for o in p["user_payload"]["options"]))
    assert any(len(set(orders)) > 1 for orders in by_scenario.values())


def test_no_real_booking_possible() -> None:
    schema = load("schemas/submit_agentic_decision.json")
    assert schema["properties"]["simulation_only"]["const"] is True
    batch = (ROOT / "data/internal/future_api_batch_preview.jsonl").read_text(encoding="utf-8")
    assert "body_preview_only" in batch


def test_counterfactual_and_placebo_checks_exist() -> None:
    rows = (ROOT / "results/robustness/confirmatory_robustness_checks.csv").read_text(encoding="utf-8")
    assert "counterfactual_rotation_candidate" in rows
    assert "placebo_ready" in rows
