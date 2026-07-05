#!/usr/bin/env python3
"""T3 support script for the §5.6 partner_position marker.

Documents the coding of `partner_position` by (a) independently
recomputing it for all 2,000 locked run-plan rows from the scenario ID,
repetition number, and the same seed formula used at plan-build time, and
confirming an exact match to the stored value, and (b) extracting its
coefficient row, verbatim, from the already-computed clustered model tables
(results/tables/confirmatory_final/table4_partner_model.csv and
table6_optimal_and_regret_models.csv) for citation in the supplement,
without re-deriving or altering those already-published estimates.

Writes PARTNER_POSITION_CHECK.md next to this script.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONF = REPO_ROOT / "confirmatory_2x2"
sys.path.insert(0, str(CONF))

from src.build_run_plan import shuffled_visible_options  # noqa: E402
from src.common import sha256_text  # noqa: E402

RUN_PLAN = CONF / "data/locked/confirmatory_run_plan.csv"
SCENARIOS_JSON = CONF / "data/locked/confirmatory_scenarios.json"
EXPERIMENT_YAML_SEED_KEY = "run_plan"
REPORT_PATH = Path(__file__).resolve().parent / "PARTNER_POSITION_CHECK.md"


def load_run_plan_seed() -> str:
    import yaml
    cfg = yaml.safe_load((CONF / "config/experiment.yaml").read_text(encoding="utf-8"))
    return cfg["random_seeds"][EXPERIMENT_YAML_SEED_KEY]


def main() -> None:
    import json

    run_plan_seed = load_run_plan_seed()
    scenarios = {s["scenario_id"]: s for s in json.loads(SCENARIOS_JSON.read_text(encoding="utf-8"))["scenarios"]}
    plan_rows = list(csv.DictReader(RUN_PLAN.open("r", encoding="utf-8")))
    assert len(plan_rows) == 2000

    mismatches = []
    positions = []
    for row in plan_rows:
        scenario = scenarios[row["scenario_id"]]
        repetition = int(row["repetition"])
        seed = int(sha256_text(f"{run_plan_seed}:{scenario['scenario_id']}:{repetition}")[:12], 16)
        _visible, _mapping, recomputed_position = shuffled_visible_options(scenario, repetition, seed)
        stored_position = int(row["partner_position"])
        positions.append(stored_position)
        if recomputed_position != stored_position:
            mismatches.append((row["observation_key"], stored_position, recomputed_position))

    from collections import Counter
    dist = Counter(positions)

    def read_coef_row(csv_path: Path, model_filter: str | None = None) -> dict[str, str]:
        with csv_path.open("r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r["term"] == "partner_position" and (model_filter is None or r.get("model") == model_filter):
                    return r
        raise AssertionError(f"partner_position row not found in {csv_path} (model={model_filter})")

    partner_model_row = read_coef_row(CONF / "results/tables/confirmatory_final/table4_partner_model.csv")
    optimal_model_row = read_coef_row(CONF / "results/tables/confirmatory_final/table6_optimal_and_regret_models.csv", "optimal_selected_logit")
    regret_model_row = read_coef_row(CONF / "results/tables/confirmatory_final/table6_optimal_and_regret_models.csv", "normalized_regret_linear")

    def dump_full_table(csv_path: Path, model_filter: str | None = None, cols: list[str] | None = None) -> list[str]:
        with csv_path.open("r", encoding="utf-8") as f:
            rows = [r for r in csv.DictReader(f) if model_filter is None or r.get("model") == model_filter]
        cols = cols or list(rows[0].keys())
        out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
        for r in rows:
            out.append("| " + " | ".join(r[c] for c in cols) + " |")
        return out

    full_tables_md = []
    full_tables_md.append("### Full table: partner_selected (scenario-clustered logistic regression)")
    full_tables_md.append("")
    full_tables_md += dump_full_table(
        CONF / "results/tables/confirmatory_final/table4_partner_model.csv",
        cols=["term", "coefficient", "se_cluster_scenario", "ci95_low", "ci95_high", "odds_ratio", "p_value"],
    )
    full_tables_md.append("")
    full_tables_md.append("### Full table: optimal_selected (scenario-clustered logistic regression)")
    full_tables_md.append("")
    full_tables_md += dump_full_table(
        CONF / "results/tables/confirmatory_final/table6_optimal_and_regret_models.csv",
        "optimal_selected_logit",
        cols=["term", "coefficient", "se_cluster_scenario", "ci95_low", "ci95_high", "odds_ratio", "p_value"],
    )
    full_tables_md.append("")
    full_tables_md.append("### Full table: normalized_regret (scenario-clustered linear regression)")
    full_tables_md.append("")
    full_tables_md += dump_full_table(
        CONF / "results/tables/confirmatory_final/table6_optimal_and_regret_models.csv",
        "normalized_regret_linear",
        cols=["term", "coefficient", "se_cluster_scenario", "ci95_low", "ci95_high", "p_value"],
    )
    (Path(__file__).resolve().parent / "FULL_COEFFICIENT_TABLES.md").write_text("\n".join(full_tables_md) + "\n", encoding="utf-8")

    lines = [
        "# PARTNER_POSITION_CHECK.md",
        "",
        "Support script for the §5.6 partner_position marker in manuscript/article.md",
        "and supplement/S4_measures_and_robustness.md §S4.3.",
        "",
        "## Recomputation of partner_position from the seed formula",
        "",
        f"Rows checked: {len(plan_rows)}",
        f"Exact matches: {len(plan_rows) - len(mismatches)}/{len(plan_rows)}",
        f"Distribution across the 10 possible positions: {dict(sorted(dist.items()))}",
        "",
    ]
    if mismatches:
        lines.append(f"**{len(mismatches)} MISMATCHES FOUND** (first 10): {mismatches[:10]}")
    else:
        lines.append("All 2,000 rows match: `partner_position` is fully reproducible from "
                      "(scenario_id, repetition) via `confirmatory_2x2/src/build_run_plan.py::shuffled_visible_options` "
                      "and the documented seed formula.")
    lines += [
        "",
        "## partner_position coefficient rows (verbatim from results/tables/confirmatory_final/, not recomputed here)",
        "",
        "| Model | coefficient | se_cluster_scenario | ci95_low | ci95_high | odds_ratio | p_value |",
        "|---|---|---|---|---|---|---|",
        f"| partner_selected (logit) | {partner_model_row['coefficient']} | {partner_model_row['se_cluster_scenario']} | {partner_model_row['ci95_low']} | {partner_model_row['ci95_high']} | {partner_model_row['odds_ratio']} | {partner_model_row['p_value']} |",
        f"| optimal_selected (logit) | {optimal_model_row['coefficient']} | {optimal_model_row['se_cluster_scenario']} | {optimal_model_row['ci95_low']} | {optimal_model_row['ci95_high']} | {optimal_model_row['odds_ratio']} | {optimal_model_row['p_value']} |",
        f"| normalized_regret (linear) | {regret_model_row['coefficient']} | {regret_model_row['se_cluster_scenario']} | {regret_model_row['ci95_low']} | {regret_model_row['ci95_high']} | n/a | {regret_model_row['p_value']} |",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")
    print(f"mismatches={len(mismatches)} distribution={dict(sorted(dist.items()))}")


if __name__ == "__main__":
    main()
