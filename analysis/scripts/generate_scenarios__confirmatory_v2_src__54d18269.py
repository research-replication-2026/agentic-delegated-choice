from __future__ import annotations

from src.common import generate_scenario_set, load_yaml, scenario_rows, visible_scenario, write_csv, write_json


def main() -> None:
    cfg = load_yaml("config/experiment.yaml")
    dev = generate_scenario_set("development", cfg["random_seeds"]["development"], cfg["scenario_counts"]["development_per_domain"])
    locked = generate_scenario_set("confirmatory", cfg["random_seeds"]["confirmatory"], cfg["scenario_counts"]["confirmatory_per_domain"])
    write_json("data/internal/development_scenarios.json", {"scenarios": dev})
    write_json("data/internal/confirmatory_scenarios_unlocked.json", {"scenarios": locked})
    write_json("data/model_visible/development_scenarios_visible.json", {"scenarios": [visible_scenario(s) for s in dev]})
    write_json("data/model_visible/confirmatory_scenarios_visible_unlocked.json", {"scenarios": [visible_scenario(s) for s in locked]})
    write_csv("data/synthetic/scenario_index.csv", scenario_rows(dev + locked))
    print(f"Generated {len(dev)} development and {len(locked)} confirmatory scenarios.")


if __name__ == "__main__":
    main()
