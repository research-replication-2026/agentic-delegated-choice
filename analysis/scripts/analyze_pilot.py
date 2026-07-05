from __future__ import annotations

import json

import pandas as pd
from pandas.errors import EmptyDataError

from src.settings import path


def descriptive_tables(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    if df.empty:
        empty = pd.DataFrame(columns=[
            "condition", "n_observations", "partner_selection_rate", "optimal_selection_rate",
            "mean_regret", "hard_constraint_violation_rate", "mean_alternatives_presented",
            "commercial_disclosure_rate", "valid_response_rate", "action_preparation_rate",
        ])
        return empty, {"commercial_effect": None, "low_agenticity_effect": None, "high_agenticity_effect": None}
    grouped = df.groupby("condition", as_index=False).agg(
        n_observations=("run_id", "count"),
        partner_selection_rate=("partner_selected", "mean"),
        optimal_selection_rate=("optimal_selected", "mean"),
        mean_regret=("normalized_regret", "mean"),
        hard_constraint_violation_rate=("hard_constraint_violation", "mean"),
        mean_alternatives_presented=("number_of_alternatives_presented", "mean"),
        commercial_disclosure_rate=("commercial_relationship_disclosed", "mean"),
        valid_response_rate=("response_valid", "mean"),
        action_preparation_rate=("action_prepared", "mean"),
    )
    neutral = df[df["commercial_incentive"] == 0]["partner_selected"].mean()
    commercial = df[df["commercial_incentive"] == 1]["partner_selected"].mean()
    effects = {
        "partner_selection_neutral": float(neutral) if pd.notna(neutral) else None,
        "partner_selection_commercial": float(commercial) if pd.notna(commercial) else None,
        "commercial_effect": float(commercial - neutral) if pd.notna(neutral) and pd.notna(commercial) else None,
    }
    for high, label in [(0, "low_agenticity_effect"), (1, "high_agenticity_effect")]:
        sub = df[df["high_agenticity"] == high]
        n = sub[sub["commercial_incentive"] == 0]["partner_selected"].mean()
        c = sub[sub["commercial_incentive"] == 1]["partner_selected"].mean()
        effects[label] = float(c - n) if pd.notna(n) and pd.notna(c) else None
    return grouped, effects


def write_analysis() -> tuple[pd.DataFrame, dict]:
    csv_path = path("data/processed/pilot_results.csv")
    try:
        df = pd.read_csv(csv_path) if csv_path.exists() and csv_path.stat().st_size > 1 else pd.DataFrame()
    except EmptyDataError:
        df = pd.DataFrame()
    table, effects = descriptive_tables(df)
    table_path = path("results/pilot/tables/descriptive_by_condition.csv")
    table.to_csv(table_path, index=False)
    with path("results/pilot/tables/effects.json").open("w", encoding="utf-8") as f:
        json.dump(effects, f, indent=2)
    return table, effects


if __name__ == "__main__":
    t, e = write_analysis()
    print(t.to_string(index=False))
    print(json.dumps(e, indent=2))
