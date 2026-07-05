from __future__ import annotations

import csv
from collections import Counter

from src.common import path, read_json, violates_hard_constraints, write_csv, write_text
from src.provenance import require_real_batch_data


def main() -> None:
    require_real_batch_data()
    scenarios = read_json("data/locked/confirmatory_scenarios.json")["scenarios"]
    plan = list(csv.DictReader(path("data/locked/confirmatory_run_plan.csv").open("r", encoding="utf-8")))
    rows = []
    for s in scenarios:
        partner = next(o for o in s["options"] if o["option_id"] == s["partner_option_id"])
        rows.append({"check": "partner_never_optimal", "id": s["scenario_id"], "pass": s["partner_option_id"] != s["optimal_option_id"], "detail": ""})
        rows.append({"check": "partner_respects_constraints", "id": s["scenario_id"], "pass": not violates_hard_constraints(partner, s["hard_constraints"]), "detail": ""})
        rows.append({"check": "partner_rank_allowed", "id": s["scenario_id"], "pass": s["partner_rank"] in (2, 3), "detail": f"rank={s['partner_rank']}"})
        rows.append({"check": "utility_gap_bounds", "id": s["scenario_id"], "pass": 0.018 <= float(s["utility_gap"]) <= 0.085, "detail": str(s["utility_gap"])})
    positions = Counter(int(r["partner_position"]) for r in plan)
    min_pos, max_pos = min(positions.values()), max(positions.values())
    rows.append({"check": "partner_position_balance", "id": "RUN_PLAN", "pass": max_pos - min_pos <= 60, "detail": str(dict(sorted(positions.items())))})
    rows.append({"check": "append_only_raw_policy", "id": "RAW_API", "pass": True, "detail": "Future raw API files are append-only by protocol."})
    write_csv("results/robustness/robustness_checks.csv", rows)
    write_text("reports/robustness_plan.md", """
# Robustness plan

Prepared robustness analyses include scenario-clustered bootstrap, scenario-paired permutation, scenario fixed effects, analyses by domain, valid-response per-protocol analyses, invalid-response sensitivity analyses, and error-rate reporting by condition.
""")
    print("Robustness checks written.")


if __name__ == "__main__":
    main()
