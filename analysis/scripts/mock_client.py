from __future__ import annotations

import json
import random
from typing import Any

from src.common import COMMERCIAL, expected_action_fields


class MockClient:
    def __init__(self, seed: int):
        self.rng = random.Random(seed)

    def decide(self, plan_row: dict[str, Any]) -> dict[str, Any]:
        visible_to_canonical = json.loads(plan_row["visible_to_canonical_json"])
        utilities = plan_row["utilities"]
        visible_ids = [o["option_id"] for o in json.loads(plan_row["visible_options_json"])]
        ranked_visible = sorted(visible_ids, key=lambda vid: utilities[visible_to_canonical[vid]], reverse=True)
        selected = ranked_visible[0]
        partner_visible = plan_row["visible_partner_option_id"]
        gap = float(plan_row["utility_gap"])
        p_partner = 0.04
        if plan_row["condition"] in COMMERCIAL:
            p_partner += 0.11 + float(plan_row["commission_rate"]) * 0.45 + max(0.0, 0.08 - gap)
            if "high" in plan_row["condition"]:
                p_partner += 0.07
        if self.rng.random() < min(0.60, p_partner):
            selected = partner_visible
        disclosed = plan_row["condition"] in COMMERCIAL and self.rng.random() < 0.45
        disclosure_text = "La plateforme peut recevoir une commission sur l'option sélectionnée." if disclosed else ""
        action_level, action_prepared, confirmation_required = expected_action_fields(plan_row["condition"])
        return {
            "scenario_id": plan_row["scenario_id"],
            "condition": plan_row["condition"],
            "selected_option_id": selected,
            "ranked_option_ids": ranked_visible,
            "criteria_used": json.loads(plan_row["criteria_json"]),
            "alternatives_presented": ranked_visible[1:4],
            "commercial_relationship_disclosed": disclosed,
            "commercial_disclosure_text": disclosure_text,
            "action_level": action_level,
            "action_prepared": action_prepared,
            "confirmation_required": confirmation_required,
            "short_rationale": "Mock local response for pipeline validation only; not confirmatory evidence.",
            "simulation_only": True,
        }
