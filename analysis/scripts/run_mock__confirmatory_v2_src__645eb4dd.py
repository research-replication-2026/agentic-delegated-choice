from __future__ import annotations

import json

from src.common import CONDITIONS, load_yaml, path, read_json, sha256_text, utc_now
from src.mock_client import MockAgentClient


def main() -> None:
    cfg = load_yaml("config/experiment.yaml")
    scenarios = read_json("data/internal/confirmatory_scenarios_locked.json")["scenarios"]
    reps = cfg["plans"]["economical"]["repetitions"]
    client = MockAgentClient(cfg["random_seeds"]["mock_run"])
    target = path("data/raw_api/mock_responses.jsonl")
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as f:
        for s in scenarios[:40]:
            for condition in CONDITIONS:
                for rep in range(reps):
                    rec = {
                        "timestamp_utc": utc_now(),
                        "scenario_id": s["scenario_id"],
                        "condition": condition,
                        "repetition": rep,
                        "seed": int(sha256_text(f"{s['scenario_id']}:{condition}:{rep}")[:8], 16),
                        "model": "mock_agent",
                        "response": client.submit_agentic_decision(s, condition, rep),
                        "latency_seconds": 0.0,
                        "input_tokens": 0,
                        "output_tokens": 0,
                    }
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"Wrote mock responses to {target}")


if __name__ == "__main__":
    main()
