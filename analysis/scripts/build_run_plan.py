from __future__ import annotations

import json
import random

from src.common import CONDITIONS, canonical_json, load_yaml, path, read_json, sha256_text, write_csv, write_text, write_xlsx


def shuffled_visible_options(scenario: dict, repetition: int, seed: int) -> tuple[list[dict], dict[str, str], int]:
    rng = random.Random(seed)
    canonical_options = list(scenario["options"])
    partner = next(o for o in canonical_options if o["option_id"] == scenario["partner_option_id"])
    others = [o for o in canonical_options if o["option_id"] != scenario["partner_option_id"]]
    rng.shuffle(others)
    partner_position = ((repetition + int(scenario["scenario_id"].split("_")[-1])) % len(canonical_options)) + 1
    ordered = others[:]
    ordered.insert(partner_position - 1, partner)
    ordered = ordered[:len(canonical_options)]
    if partner not in ordered:
        ordered[-1] = partner
    visible_ids = []
    while len(visible_ids) < len(ordered):
        candidate = f"V{rng.randint(100, 999)}"
        if candidate not in visible_ids:
            visible_ids.append(candidate)
    mapping = {option["option_id"]: visible_id for option, visible_id in zip(ordered, visible_ids)}
    visible_options = []
    for position, (option, visible_id) in enumerate(zip(ordered, visible_ids), start=1):
        visible_options.append({
            "option_id": visible_id,
            "name": option["name"],
            "attributes": option["attributes"],
            "catalog_position": position,
        })
    return visible_options, mapping, next(o["catalog_position"] for o in visible_options if o["option_id"] == mapping[scenario["partner_option_id"]])


def user_prompt(scenario: dict, visible_options: list[dict]) -> str:
    payload = {
        "scenario_id": scenario["scenario_id"],
        "user_request": scenario["user_request"],
        "primary_criteria": scenario["primary_criteria"],
        "secondary_criteria": scenario["secondary_criteria"],
        "hard_constraints": scenario["hard_constraints"],
        "options": visible_options,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def main() -> None:
    cfg = load_yaml("config/experiment.yaml")
    scenarios = read_json("data/locked/confirmatory_scenarios.json")["scenarios"]
    reps = cfg["repetitions_per_scenario_condition"]
    rows = []
    jsonl_lines = []
    for scenario in scenarios:
        for repetition in range(1, reps + 1):
            seed = int(sha256_text(f"{cfg['random_seeds']['run_plan']}:{scenario['scenario_id']}:{repetition}")[:12], 16)
            visible_options, mapping, partner_position = shuffled_visible_options(scenario, repetition, seed)
            inverse_mapping = {v: k for k, v in mapping.items()}
            prompt = user_prompt(scenario, visible_options)
            for condition in CONDITIONS:
                observation_key = f"{scenario['scenario_id']}__{condition}__rep{repetition:02d}"
                row = {
                    "observation_key": observation_key,
                    "scenario_id": scenario["scenario_id"],
                    "condition": condition,
                    "repetition": repetition,
                    "domain": scenario["domain"],
                    "commission_rate": scenario["commission_rate"],
                    "utility_gap": scenario["utility_gap"],
                    "optimal_option_id": scenario["optimal_option_id"],
                    "partner_option_id": scenario["partner_option_id"],
                    "visible_optimal_option_id": mapping[scenario["optimal_option_id"]],
                    "visible_partner_option_id": mapping[scenario["partner_option_id"]],
                    "partner_position": partner_position,
                    "random_seed": seed,
                    "visible_to_canonical_json": canonical_json(inverse_mapping),
                    "visible_options_json": canonical_json(visible_options),
                    "user_prompt": prompt,
                }
                rows.append(row)
                jsonl_lines.append(row)
    run_plan_hash = sha256_text(canonical_json(rows))
    write_csv("data/locked/confirmatory_run_plan.csv", rows)
    write_xlsx("data/locked/confirmatory_run_plan.xlsx", rows)
    target = "data/locked/confirmatory_run_plan.jsonl"
    path(target).parent.mkdir(parents=True, exist_ok=True)
    with path(target).open("w", encoding="utf-8") as f:
        for row in jsonl_lines:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    write_text("data/locked/RUN_PLAN_HASH.txt", run_plan_hash)
    print(f"Built run plan with {len(rows)} observations: {run_plan_hash}")


if __name__ == "__main__":
    main()
