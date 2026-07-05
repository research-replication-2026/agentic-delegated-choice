from __future__ import annotations

import json
from datetime import datetime, timezone

import pandas as pd
from pandas.errors import EmptyDataError

from src.analyze_pilot import descriptive_tables
from src.settings import path, sha256_file


DISCLAIMER = (
    "This pilot is a technical and methodological validation exercise. It is not the confirmatory experiment "
    "and should not be interpreted as providing definitive evidence for or against the hypotheses."
)


def _read_df() -> pd.DataFrame:
    csv_path = path("data/processed/pilot_results.csv")
    try:
        return pd.read_csv(csv_path) if csv_path.exists() and csv_path.stat().st_size > 1 else pd.DataFrame()
    except EmptyDataError:
        return pd.DataFrame()


def write_reports(model: str | None = None, run_stats: dict | None = None, remaining_problem: str = "") -> None:
    df = _read_df()
    table, effects = descriptive_tables(df)
    valid_rate = float(df["response_valid"].mean()) if not df.empty and "response_valid" in df else 0.0
    calls = len(df)
    input_tokens = int(df["input_tokens"].fillna(0).sum()) if not df.empty and "input_tokens" in df else 0
    output_tokens = int(df["output_tokens"].fillna(0).sum()) if not df.empty and "output_tokens" in df else 0
    model_value = model or (df["model"].dropna().iloc[0] if not df.empty and "model" in df and df["model"].notna().any() else "not executed")
    table_md = table.to_string(index=False) if not table.empty else "No API observations were available for descriptive analysis."
    report = f"""# Pilot report

## 1. Objective
Empirically validate a small pilot for testing whether a commercial incentive shifts hotel recommendations by an AI agent.

## 2. Design
Factorial 2 x 2 design: neutral/commercial incentive crossed with low/high agenticity. Five synthetic scenarios produce 20 planned observations.

## 3. Scenarios
Five synthetic hotel-selection scenarios were generated with fixed seed 20260629. Each scenario includes eight fictional hotels, hard constraints, weighted objective utility, an independently selected optimal option, and a non-optimal partner option ranked second or third.

## 4. Model used
{model_value}

## 5. Number of calls
Planned observations: {(run_stats or {}).get("planned", 20)}. Successful API observations in processed data: {calls}.

## 6. Valid response rate
{valid_rate:.3f}

## 7. Descriptive results
{table_md}

## 8. Initial elements on H1
Commercial minus neutral partner-selection rate: {effects.get("commercial_effect")}.

## 9. Initial elements on H2
Low-agenticity commercial effect: {effects.get("low_agenticity_effect")}. High-agenticity commercial effect: {effects.get("high_agenticity_effect")}.

## 10. Initial elements on H3
Mean normalized regret by condition is reported descriptively in the table. This pilot cannot confirm H3.

## 11. Observed anomalies
{remaining_problem or "No anomaly recorded beyond the small pilot scale and any API/format errors listed in the processed dataset."}

## 12. Structured output quality
Structured outputs were parsed deterministically from raw JSONL records. Tool calls, when present, were parsed separately.

## 13. Token cost estimate
Input tokens recorded: {input_tokens}. Output tokens recorded: {output_tokens}. This is a token-volume summary, not a monetary price estimate.

## 14. Recommendations before full experiment
Increase scenario count, lock the model, pre-register the analysis plan, inspect malformed outputs, and run a small calibration batch before any 2,000-call experiment.

## 15. Pilot limits
{DISCLAIMER}
"""
    path("reports/pilot_report.md").write_text(report, encoding="utf-8")
    hashes = {}
    hash_path = path("results/pilot/hashes.json")
    if hash_path.exists():
        hashes = json.loads(hash_path.read_text(encoding="utf-8"))
    methods = f"""# Pilot methods

Executed at: {datetime.now(timezone.utc).isoformat()}

Working directory: {path('').resolve()}

Files generated:
- data/synthetic/pilot_scenarios.csv
- data/synthetic/pilot_scenarios.json
- data/raw_api/pilot_responses.jsonl
- data/processed/pilot_results.csv
- data/processed/pilot_results.xlsx
- results/pilot/tables/descriptive_by_condition.csv
- results/pilot/figures/*.png
- results/pilot/figures/*.pdf

Execution summary:
{json.dumps(run_stats or {}, indent=2)}

Hashes:
{json.dumps(hashes, indent=2)}

No real booking service was connected. The `prepare_booking` tool is a local schema supplied to the model and cannot execute external actions.
"""
    path("reports/pilot_methods.md").write_text(methods, encoding="utf-8")


if __name__ == "__main__":
    write_reports()
    print("Reports written")
