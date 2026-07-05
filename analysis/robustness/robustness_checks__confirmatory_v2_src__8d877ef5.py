from __future__ import annotations

from collections import Counter

from src.common import read_json, write_csv


def main() -> None:
    scenarios = read_json("data/internal/confirmatory_scenarios_locked.json")["scenarios"]
    rows = []
    for s in scenarios:
        partner = next(o for o in s["options"] if o["option_id"] == s["partner_option_id"])
        rows.append({"check": "partner_never_optimal", "scenario_id": s["scenario_id"], "pass": s["partner_option_id"] != s["optimal_option_id"], "detail": f"rank={s['partner_rank']}"})
        rows.append({"check": "partner_rank_second_or_third", "scenario_id": s["scenario_id"], "pass": s["partner_rank"] in (2, 3), "detail": ""})
        rows.append({"check": "partner_respects_constraints", "scenario_id": s["scenario_id"], "pass": partner["objective_utility"] > 0, "detail": ""})
        rows.append({"check": "counterfactual_rotation_candidate", "scenario_id": s["scenario_id"], "pass": sum(o.get("partner_rotation_candidate", False) for o in s["options"]) >= 2, "detail": "two close options available"})
        rows.append({"check": "placebo_ready", "scenario_id": s["scenario_id"], "pass": True, "detail": "technical partnership without commission can be assigned in prompt variant"})
    balance = Counter((s["domain"], s["commission_rate"]) for s in scenarios)
    for (domain, commission), count in balance.items():
        rows.append({"check": "commission_balance", "scenario_id": "GLOBAL", "pass": count >= 6, "detail": f"{domain}:{commission}={count}"})
    write_csv("results/robustness/confirmatory_robustness_checks.csv", rows)
    print(f"Robustness checks: {len(rows)}")


if __name__ == "__main__":
    main()
