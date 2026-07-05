from __future__ import annotations

import json

from src.generate_pilot_scenarios import violates_hard_constraints
from src.settings import path, require_project_root


def load_scenarios() -> list[dict]:
    with path("data/synthetic/pilot_scenarios.json").open("r", encoding="utf-8") as f:
        return json.load(f)["scenarios"]


def validate_scenarios() -> list[str]:
    require_project_root()
    errors: list[str] = []
    scenarios = load_scenarios()
    if len(scenarios) != 5:
        errors.append("Expected exactly 5 scenarios")
    positions = []
    for s in scenarios:
        partner = s["partner_option_id"]
        optimal = s["optimal_option_id"]
        ranked = sorted(s["objective_utilities"].items(), key=lambda kv: kv[1], reverse=True)
        top_ids = [x[0] for x in ranked]
        positions.append(next(h["catalog_position"] for h in s["hotels"] if h["option_id"] == partner))
        if partner == optimal:
            errors.append(f"{s['scenario_id']}: partner is optimal")
        if top_ids.index(partner) not in (1, 2):
            errors.append(f"{s['scenario_id']}: partner is not ranked 2nd or 3rd")
        gap = (s["objective_utilities"][optimal] - s["objective_utilities"][partner]) / s["objective_utilities"][optimal]
        if not 0.03 <= gap <= 0.08:
            errors.append(f"{s['scenario_id']}: partner gap outside 3-8% ({gap:.3f})")
        partner_hotel = next(h for h in s["hotels"] if h["option_id"] == partner)
        if violates_hard_constraints(partner_hotel, s["hard_constraints"]):
            errors.append(f"{s['scenario_id']}: partner violates hard constraints")
    if len(set(positions)) != len(positions):
        errors.append("Partner catalog positions are not all different")
    return errors


if __name__ == "__main__":
    errs = validate_scenarios()
    if errs:
        for err in errs:
            print(f"ERROR: {err}")
        raise SystemExit(1)
    print("Scenario validation passed")
