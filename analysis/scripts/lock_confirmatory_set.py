from __future__ import annotations

from src.common import canonical_json, read_json, scenario_rows, sha256_text, visible_scenario, write_csv, write_json


def main() -> None:
    scenarios = read_json("data/internal/confirmatory_scenarios_unlocked.json")["scenarios"]
    global_hash = sha256_text(canonical_json(scenarios))
    lock = {
        "locked": True,
        "global_hash": global_hash,
        "scenario_count": len(scenarios),
        "scenarios": scenarios,
    }
    write_json("data/internal/confirmatory_scenarios_locked.json", lock)
    write_json("data/model_visible/confirmatory_scenarios_visible_locked.json", {"global_hash": global_hash, "scenarios": [visible_scenario(s) for s in scenarios]})
    write_csv("data/synthetic/confirmatory_locked_index.csv", scenario_rows(scenarios))
    print(f"Locked {len(scenarios)} scenarios with hash {global_hash}")


if __name__ == "__main__":
    main()
