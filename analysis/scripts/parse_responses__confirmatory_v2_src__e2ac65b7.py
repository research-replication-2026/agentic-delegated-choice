from __future__ import annotations

import json

from src.common import path, write_csv


def main() -> None:
    raw = path("data/raw_api/mock_responses.jsonl")
    rows = []
    with raw.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, 1):
            rec = json.loads(line)
            response = rec.get("response", {})
            rows.append({
                "observation_key": f"{rec['scenario_id']}__{rec['condition']}__rep{rec['repetition']}",
                "line_number": line_number,
                "scenario_id": rec["scenario_id"],
                "condition": rec["condition"],
                "repetition": rec["repetition"],
                "model": rec["model"],
                "response_valid": response.get("simulation_only") is True,
                "selected_option_id": response.get("selected_option_id", ""),
                "ranked_option_ids": "|".join(response.get("ranked_option_ids", [])),
                "alternatives_presented": "|".join(response.get("alternatives_presented", [])),
                "commercial_relationship_disclosed": response.get("commercial_relationship_disclosed", False),
                "commercial_disclosure_text": response.get("commercial_disclosure_text", ""),
                "commission_rate_disclosed": response.get("commission_rate_disclosed", False),
                "action_level": response.get("action_level", ""),
                "action_prepared": response.get("action_prepared", False),
                "confirmation_required": response.get("confirmation_required", False),
                "latency_seconds": rec.get("latency_seconds", 0),
                "input_tokens": rec.get("input_tokens", 0),
                "output_tokens": rec.get("output_tokens", 0),
            })
    write_csv("data/processed/mock_parsed.csv", rows)
    print(f"Parsed {len(rows)} mock responses.")


if __name__ == "__main__":
    main()
