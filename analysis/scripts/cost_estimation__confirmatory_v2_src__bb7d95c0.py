from __future__ import annotations

import csv

from src.common import PILOT_ROOT, load_yaml, write_csv


def pilot_token_means() -> tuple[float, float]:
    target = PILOT_ROOT / "data/processed/pilot_results.csv"
    rows = list(csv.DictReader(target.open("r", encoding="utf-8")))
    input_mean = sum(float(r["input_tokens"]) for r in rows) / len(rows)
    output_mean = sum(float(r["output_tokens"]) for r in rows) / len(rows)
    return input_mean, output_mean


def main() -> None:
    cfg = load_yaml("config/experiment.yaml")
    pricing = load_yaml("config/pricing.yaml")
    in_mean, out_mean = pilot_token_means()
    price = pricing["models"][pricing["default_model"]]
    per_obs = in_mean / 1_000_000 * price["input_per_1m_tokens"] + out_mean / 1_000_000 * price["output_per_1m_tokens"]
    rows = []
    for name, plan in cfg["plans"].items():
        observations = plan["scenarios"] * plan["conditions"] * plan["repetitions"]
        rows.append({
            "plan": name,
            "observations": observations,
            "mean_input_tokens_from_pilot": round(in_mean, 2),
            "mean_output_tokens_from_pilot": round(out_mean, 2),
            "estimated_cost_per_observation": round(per_obs, 6),
            "estimated_cost": round(per_obs * observations, 2),
            "estimated_cost_with_20pct_margin": round(per_obs * observations * (1 + pricing["safety_margin"]), 2),
            "pricing_manual_verification_required": True,
        })
    write_csv("results/tables/cost_estimation.csv", rows)
    print("Cost estimation written.")


if __name__ == "__main__":
    main()
