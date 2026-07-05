from __future__ import annotations

import csv
import json

from src.common import load_yaml, now_utc, path, read_json, sha256_text
from src.mock_client import MockClient


def main() -> None:
    cfg = load_yaml("config/experiment.yaml")
    scenarios = {s["scenario_id"]: s for s in read_json("data/locked/confirmatory_scenarios.json")["scenarios"]}
    rows = list(csv.DictReader(path("data/locked/confirmatory_run_plan.csv").open("r", encoding="utf-8")))
    client = MockClient(cfg["random_seeds"]["mock"])
    target = path("data/raw_api/mock_responses.jsonl")
    with target.open("w", encoding="utf-8") as f:
        for row in rows:
            scenario = scenarios[row["scenario_id"]]
            enriched = dict(row)
            enriched["utilities"] = scenario["objective_utilities"]
            enriched["criteria_json"] = json.dumps(scenario["primary_criteria"] + scenario["secondary_criteria"], ensure_ascii=False)
            attempt_id = sha256_text(f"mock:{row['observation_key']}:1")[:20]
            rec = {
                "timestamp_utc": now_utc(),
                "observation_key": row["observation_key"],
                "attempt_id": attempt_id,
                "attempt_number": 1,
                "scenario_id": row["scenario_id"],
                "condition": row["condition"],
                "repetition": int(row["repetition"]),
                "model": "mock_client",
                "latency_seconds": 0.0,
                "input_tokens": 0,
                "output_tokens": 0,
                "response": client.decide(enriched),
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"Mock responses written: {target}")


if __name__ == "__main__":
    main()
