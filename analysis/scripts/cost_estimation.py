from __future__ import annotations

import csv

from src.common import PROJECT_ROOT, load_yaml, write_csv, write_text


def pilot_token_means() -> tuple[float, float]:
    target = PROJECT_ROOT / "data/processed/pilot_results.csv"
    rows = list(csv.DictReader(target.open("r", encoding="utf-8")))
    return (
        sum(float(r["input_tokens"]) for r in rows) / len(rows),
        sum(float(r["output_tokens"]) for r in rows) / len(rows),
    )


def main() -> None:
    pricing = load_yaml("config/pricing.yaml")
    input_mean, output_mean = pilot_token_means()
    std = pricing["standard_api"]
    per_obs = input_mean / 1_000_000 * std["input_per_1m_tokens"] + output_mean / 1_000_000 * std["output_per_1m_tokens"]
    observations = 2000
    batch_cost = per_obs * observations * pricing["batch_api_discount"]
    rows = [{
        "observations": observations,
        "mean_input_tokens": round(input_mean, 2),
        "mean_output_tokens": round(output_mean, 2),
        "standard_cost_per_observation": round(per_obs, 6),
        "standard_cost_2000": round(per_obs * observations, 2),
        "batch_cost_2000": round(batch_cost, 2),
        "standard_cost_with_20pct_margin": round(per_obs * observations * (1 + pricing["safety_margin"]), 2),
        "batch_cost_with_20pct_margin": round(batch_cost * (1 + pricing["safety_margin"]), 2),
        "manual_tariff_verification_required": True,
    }]
    write_csv("results/tables/cost_estimation.csv", rows)
    r = rows[0]
    write_text("reports/cost_estimation.md", f"""
# Cost estimation

Token estimates use the existing pilot file `data/processed/pilot_results.csv`. Prices are read from `config/pricing.yaml` and are placeholders that must be manually verified before any real launch.

| Metric | Value |
| --- | --- |
| Mean input tokens | {r['mean_input_tokens']} |
| Mean output tokens | {r['mean_output_tokens']} |
| Standard cost per observation | {r['standard_cost_per_observation']} |
| Standard cost for 2,000 observations | {r['standard_cost_2000']} |
| Batch API cost for 2,000 observations | {r['batch_cost_2000']} |
| Standard cost with 20% margin | {r['standard_cost_with_20pct_margin']} |
| Batch cost with 20% margin | {r['batch_cost_with_20pct_margin']} |

No API call is used to obtain tariffs.
""")
    print("Cost estimation written.")


if __name__ == "__main__":
    main()
