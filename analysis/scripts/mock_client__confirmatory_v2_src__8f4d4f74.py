from __future__ import annotations

import random
from typing import Any

from src.common import condition_parts, ranked_ids


class MockAgentClient:
    """Deterministic local stand-in for future API clients."""

    def __init__(self, seed: int = 20260704):
        self.rng = random.Random(seed)

    def submit_agentic_decision(self, scenario: dict[str, Any], condition: str, repetition: int = 0) -> dict[str, Any]:
        commercial, agenticity = condition_parts(condition)
        ranked = ranked_ids(scenario)
        selected = ranked[0]
        partner = scenario["partner_option_id"]
        gap = scenario["partner_utility_gap"]
        p_partner = 0.05
        if commercial == "C1":
            p_partner += 0.02
        if commercial == "C2":
            p_partner += max(0.04, 0.22 - gap)
            if agenticity == "A1":
                p_partner += 0.06
            p_partner += scenario["commission_rate"] * 0.5
        if self.rng.random() < min(p_partner, 0.65):
            selected = partner
        disclosure = commercial in {"C1", "C2"} and (commercial == "C1" or self.rng.random() < 0.65)
        rate_disclosed = disclosure and self.rng.random() < (0.8 if commercial == "C1" else 0.45)
        text = ""
        if disclosure:
            text = "A commercial relationship exists"
            if rate_disclosed:
                text += f" with a {int(scenario['commission_rate'] * 100)}% commission and possible conflict of interest"
        return {
            "scenario_id": scenario["scenario_id"],
            "selected_option_id": selected,
            "ranked_option_ids": ranked,
            "criteria_used": scenario["primary_criteria"] + scenario["secondary_criteria"],
            "inferred_preferences": scenario["primary_criteria"],
            "alternatives_presented": ranked[1:4],
            "commercial_relationship_disclosed": disclosure,
            "commercial_disclosure_text": text,
            "commission_rate_disclosed": rate_disclosed,
            "action_level": "booking_preparation" if agenticity == "A1" else "recommendation",
            "action_prepared": agenticity == "A1",
            "confirmation_required": agenticity == "A1",
            "short_rationale": "Mock local decision based on objective utility and preregistered condition parameters.",
            "simulation_only": True,
        }
