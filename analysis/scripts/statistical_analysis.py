from __future__ import annotations

import csv
from collections import Counter, defaultdict

from src.common import path, write_csv, write_text
from src.provenance import require_real_batch_data


def load_available_results() -> tuple[str, list[dict[str, str]]]:
    confirmatory = path("data/processed/confirmatory_results.csv")
    if not confirmatory.exists():
        print("REAL BATCH DATA REQUIRED")
        raise SystemExit("REAL BATCH DATA REQUIRED: confirmatory_results.csv is missing.")
    rows = [r for r in csv.DictReader(confirmatory.open("r", encoding="utf-8")) if r.get("response_valid") == "1"]
    if not rows:
        print("REAL BATCH DATA REQUIRED")
        raise SystemExit("REAL BATCH DATA REQUIRED: no valid confirmatory result rows.")
    return "confirmatory", rows


def prop(rows: list[dict[str, str]], condition: str, outcome: str) -> float:
    subset = [r for r in rows if r["condition"] == condition]
    return sum(int(r[outcome]) for r in subset) / len(subset) if subset else 0.0


def main() -> None:
    require_real_batch_data()
    source, rows = load_available_results()
    summary = []
    for condition in ["neutral_low_agenticity", "commercial_low_agenticity", "neutral_high_agenticity", "commercial_high_agenticity"]:
        subset = [r for r in rows if r["condition"] == condition]
        summary.append({
            "source": source,
            "condition": condition,
            "n_valid": len(subset),
            "partner_selection_rate": round(prop(rows, condition, "partner_selected"), 4),
            "optimal_selection_rate": round(prop(rows, condition, "optimal_selected"), 4),
        })
    low = prop(rows, "commercial_low_agenticity", "partner_selected") - prop(rows, "neutral_low_agenticity", "partner_selected")
    high = prop(rows, "commercial_high_agenticity", "partner_selected") - prop(rows, "neutral_high_agenticity", "partner_selected")
    summary.append({"source": source, "condition": "h2_difference_in_differences", "n_valid": len(rows), "partner_selection_rate": round(high - low, 4), "optimal_selection_rate": ""})
    write_csv(f"results/tables/{source}_descriptive_analysis.csv", summary)
    by_domain = []
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["domain"]].append(row)
    for domain, domain_rows in grouped.items():
        by_domain.append({
            "source": source,
            "domain": domain,
            "neutral_rate": round((prop(domain_rows, "neutral_low_agenticity", "partner_selected") + prop(domain_rows, "neutral_high_agenticity", "partner_selected")) / 2, 4),
            "commercial_rate": round((prop(domain_rows, "commercial_low_agenticity", "partner_selected") + prop(domain_rows, "commercial_high_agenticity", "partner_selected")) / 2, 4),
        })
    write_csv(f"results/tables/{source}_domain_results.csv", by_domain)
    write_text("reports/statistical_analysis_plan.md", """
# Statistical analysis implementation plan

Primary model:

`partner_selected ~ commercial_condition * high_agenticity + utility_gap + commission_rate_in_commercial_condition + domain + partner_position + scenario fixed effects`

When mixed logistic regression is available, the scenario term should be specified as `(1 | scenario_id)`. The repository also prepares scenario fixed effects, scenario-clustered standard errors, and clustered bootstrap robustness.

H1 is the main commercial-condition effect. H2 is the commercial-condition by high-agenticity interaction. H3a repeats the model for `optimal_selected`. H3b uses `normalized_regret` with the same fixed effects. Secondary outcomes receive Benjamini-Hochberg correction.
""")
    print(f"Statistical analysis prepared from {source} data.")


if __name__ == "__main__":
    main()
