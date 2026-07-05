from __future__ import annotations

from src.common import canonical_json, read_json, scenario_index_rows, sha256_text, visible_scenario, write_csv, write_json, write_text, write_xlsx


def main() -> None:
    scenarios = read_json("data/locked/confirmatory_scenarios_draft.json")["scenarios"]
    locked_hash = sha256_text(canonical_json(scenarios))
    payload = {"locked": True, "scenario_count": len(scenarios), "global_sha256": locked_hash, "scenarios": scenarios}
    rows = scenario_index_rows(scenarios)
    write_json("data/locked/confirmatory_scenarios.json", payload)
    write_csv("data/locked/confirmatory_scenarios.csv", rows)
    write_xlsx("data/locked/confirmatory_scenarios.xlsx", rows)
    write_json("data/model_visible/confirmatory_scenarios_visible.json", {"global_sha256": locked_hash, "scenarios": [visible_scenario(s) for s in scenarios]})
    write_text("data/locked/LOCKED_SET_HASH.txt", locked_hash)
    print(f"Locked {len(scenarios)} scenarios: {locked_hash}")


if __name__ == "__main__":
    main()
