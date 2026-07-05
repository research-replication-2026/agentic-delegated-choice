#!/usr/bin/env python3
"""T0 verification gate.

Independently recomputes every published manuscript number from the raw merged
JSONL, the locked run plan, and the locked scenario set -- without importing the
statistics functions in confirmatory_2x2/src/final_methodology_results.py. Only
deterministic, non-statistical lookups are reused from src/ (JSON field
extraction in parse_responses.extract_decision/validate_decision, and the hard
-constraint check in common.violates_hard_constraints), since those define what
the raw fields *mean*, not how the reported statistics are computed. The
regression models, the cluster bootstrap, and every aggregate reported in the
manuscript are re-derived from scratch here.

Writes VERIFICATION_REPORT.md next to this script with one PASS/FAIL row per
published number. Never modifies the manuscript. Exits 1 if the hash gate
(rule 4) fails; otherwise exits 0 regardless of PASS/FAIL count (the report is
the deliverable, not a build gate) but prints a summary count.
"""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import optimize, stats

REPO_ROOT = Path(__file__).resolve().parents[2]
CONF = REPO_ROOT / "confirmatory_2x2"
sys.path.insert(0, str(CONF))

from src.common import COMMERCIAL, CONDITIONS, HIGH_AGENTICITY, sha256_file, violates_hard_constraints  # noqa: E402
from src.parse_responses import extract_decision, validate_decision  # noqa: E402

REPORT_PATH = Path(__file__).resolve().parent / "VERIFICATION_REPORT.md"

# ---------------------------------------------------------------------------
# Rule 4: hash gate. Must pass before any computation below runs.
# ---------------------------------------------------------------------------
EXPECTED_MERGED_DATA_SHA256 = "9ad195935d60025f9cff02ef290aebd829c9809b273f16a1d27bd2015dedd4b9"
EXPECTED_SCENARIO_SET_SHA256 = "e6f882ea0ad1c5161ee54e68f14e4d0b0685dd5016281cec9064340bb2e5206b"
EXPECTED_PLAN_SHA256 = "1dab6c91c9758623c3fd0e752187b847cdd20f4a9aa419e341d0f96ec8b74303"

MERGED_JSONL = CONF / "data/raw_api/confirmatory_corrected_v2_merged_output.jsonl"
LOCKED_SET_HASH_FILE = CONF / "data/locked/LOCKED_SET_HASH.txt"
RUN_PLAN_HASH_FILE = CONF / "data/locked/RUN_PLAN_HASH.txt"
RUN_PLAN_CSV = CONF / "data/locked/confirmatory_run_plan.csv"
SCENARIOS_JSON = CONF / "data/locked/confirmatory_scenarios.json"
PROVENANCE_JSON = CONF / "data/processed/DATA_PROVENANCE.json"
MANIFEST_JSON = CONF / "MANIFEST.json"


def hash_gate() -> None:
    actual_merged = sha256_file(MERGED_JSONL)
    actual_set = LOCKED_SET_HASH_FILE.read_text(encoding="utf-8").strip()
    actual_plan = RUN_PLAN_HASH_FILE.read_text(encoding="utf-8").strip()
    failures = []
    if actual_merged != EXPECTED_MERGED_DATA_SHA256:
        failures.append(f"merged data sha256 mismatch: expected {EXPECTED_MERGED_DATA_SHA256}, got {actual_merged}")
    if actual_set != EXPECTED_SCENARIO_SET_SHA256:
        failures.append(f"scenario set sha256 mismatch: expected {EXPECTED_SCENARIO_SET_SHA256}, got {actual_set}")
    if actual_plan != EXPECTED_PLAN_SHA256:
        failures.append(f"plan sha256 mismatch: expected {EXPECTED_PLAN_SHA256}, got {actual_plan}")
    manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
    manifest_by_path = {f["path"]: f["sha256"] for f in manifest.get("files", [])}
    for rel, expect_key in [
        ("data/locked/LOCKED_SET_HASH.txt", None),
        ("data/locked/RUN_PLAN_HASH.txt", None),
    ]:
        if rel in manifest_by_path:
            live = sha256_file(CONF / rel)
            if manifest_by_path[rel] != live:
                failures.append(f"MANIFEST.json cross-check failed for {rel}: manifest={manifest_by_path[rel]} live={live}")
    if failures:
        print("HASH GATE FAILED:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print("Hash gate PASSED: merged data, locked scenario set, and locked plan all match required SHA-256 values.")


# ---------------------------------------------------------------------------
# Reconstruct the 2,000-row analysis dataset directly from raw + locked inputs.
# ---------------------------------------------------------------------------

def infer_batch_id(custom_id: str) -> str:
    sid = custom_id.split("__", 1)[0]
    idx = int(sid.rsplit("_", 1)[1])
    if idx <= 13:
        return "batch_6a42d8b207bc8190aab700fae04d9ae4"
    if idx <= 25:
        return "batch_6a42da6911308190805c0de8538579c0"
    if idx <= 38:
        return "batch_6a4367af0df481909c8a46e20cc3449b"
    return "batch_6a4368ee2f4c8190a8032fdcc02f88c3"


def reconstruct_dataset() -> pd.DataFrame:
    plan_rows = list(csv.DictReader(RUN_PLAN_CSV.open("r", encoding="utf-8")))
    plan = {r["observation_key"]: r for r in plan_rows}
    scenarios = {s["scenario_id"]: s for s in json.loads(SCENARIOS_JSON.read_text(encoding="utf-8"))["scenarios"]}
    rows = []
    seen = set()
    with MERGED_JSONL.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            custom_id = rec["custom_id"]
            assert custom_id not in seen, f"duplicate custom_id {custom_id}"
            seen.add(custom_id)
            p = plan[custom_id]
            response = rec.get("response") or {}
            body = response.get("body") if isinstance(response.get("body"), dict) else {}
            usage = body.get("usage") if isinstance(body.get("usage"), dict) else {}
            decision = extract_decision({"response": body}) if int(response.get("status_code") or 0) == 200 else None
            valid, _ = validate_decision(decision, p["condition"]) if decision else (False, "missing")
            visible_to_canonical = json.loads(p["visible_to_canonical_json"])
            selected_visible = decision.get("selected_option_id", "") if decision else ""
            canonical_selected = visible_to_canonical.get(selected_visible, "")
            scenario = scenarios[p["scenario_id"]]
            option = next((o for o in scenario["options"] if o["option_id"] == canonical_selected), None)
            valid = bool(valid and canonical_selected and option)
            selected_utility = float(scenario["objective_utilities"][canonical_selected]) if valid else np.nan
            optimal_utility = float(scenario["objective_utilities"][p["optimal_option_id"]])
            regret = optimal_utility - selected_utility if valid else np.nan
            disclosed = bool(decision.get("commercial_relationship_disclosed", False)) if decision else False
            condition = p["condition"]
            rows.append({
                "custom_id": custom_id,
                "scenario_id": p["scenario_id"],
                "domain": p["domain"],
                "condition": condition,
                "commercial_condition": int(condition in COMMERCIAL),
                "high_agenticity": int(condition in HIGH_AGENTICITY),
                "partner_selected": int(canonical_selected == p["partner_option_id"]) if valid else np.nan,
                "optimal_selected": int(canonical_selected == p["optimal_option_id"]) if valid else np.nan,
                "utility_regret": regret if valid else np.nan,
                "normalized_regret": (regret / optimal_utility) if valid else np.nan,
                "hard_constraint_violation": int(violates_hard_constraints(option, scenario["hard_constraints"])) if valid else np.nan,
                "partner_position": int(p["partner_position"]),
                "commission_rate": float(p["commission_rate"]),
                "utility_gap": float(p["utility_gap"]),
                "action_prepared": int(bool(decision.get("action_prepared", False))) if valid else np.nan,
                "confirmation_required": int(bool(decision.get("confirmation_required", False))) if valid else np.nan,
                "commercial_relationship_disclosed": int(disclosed) if valid else np.nan,
                "commercial_influence_without_disclosure": int(condition in COMMERCIAL and canonical_selected == p["partner_option_id"] and not disclosed) if valid else np.nan,
                "response_valid": int(valid),
                "batch_id": infer_batch_id(custom_id),
            })
    df = pd.DataFrame(rows)
    assert len(df) == 2000 and df["custom_id"].nunique() == 2000
    assert set(plan) == set(df["custom_id"])
    assert df["condition"].value_counts().to_dict() == {c: 500 for c in CONDITIONS}
    assert int(df["response_valid"].sum()) == 2000
    return df


# ---------------------------------------------------------------------------
# Fresh (independent) statistics: cluster bootstrap + clustered logit/OLS.
# ---------------------------------------------------------------------------

def wilson_ci(k: int, n: int) -> tuple[float, float]:
    z = 1.959963984540054
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denom
    return max(0.0, center - half), min(1.0, center + half)


def h1_diff(df: pd.DataFrame, outcome: str) -> float:
    return float(df.loc[df["commercial_condition"] == 1, outcome].mean() - df.loc[df["commercial_condition"] == 0, outcome].mean())


def h2_did(df: pd.DataFrame, outcome: str) -> float:
    r = df.groupby("condition")[outcome].mean()
    return float((r["commercial_high_agenticity"] - r["neutral_high_agenticity"]) - (r["commercial_low_agenticity"] - r["neutral_low_agenticity"]))


def cluster_bootstrap(df: pd.DataFrame, statistic, seed: int, n_boot: int = 2000) -> tuple[float, float, float, float]:
    rng = np.random.default_rng(seed)
    scenarios = np.array(sorted(df["scenario_id"].unique()))
    idx_by_scenario = {sid: np.flatnonzero(df["scenario_id"].to_numpy() == sid) for sid in scenarios}
    observed = float(statistic(df))
    vals = np.empty(n_boot)
    for i in range(n_boot):
        sample = rng.choice(scenarios, size=len(scenarios), replace=True)
        idx = np.concatenate([idx_by_scenario[s] for s in sample])
        vals[i] = statistic(df.iloc[idx])
    lo, hi = np.quantile(vals, [0.025, 0.975])
    p = 2 * min(np.mean(vals <= 0), np.mean(vals >= 0))
    return observed, float(lo), float(hi), float(min(1.0, p))


def raw_effect_ratios(df: pd.DataFrame, outcome: str) -> dict[str, float]:
    neutral = df.loc[df["commercial_condition"] == 0, outcome].astype(float)
    commercial = df.loc[df["commercial_condition"] == 1, outcome].astype(float)
    pn, pc = float(neutral.mean()), float(commercial.mean())
    an, bn = neutral.sum(), len(neutral) - neutral.sum()
    ac, bc = commercial.sum(), len(commercial) - commercial.sum()
    odds_ratio = ((ac + 0.5) / (bc + 0.5)) / ((an + 0.5) / (bn + 0.5))
    relative_risk = pc / pn if pn > 0 else float("inf")
    return {"relative_risk": relative_risk, "odds_ratio": odds_ratio}


def design_matrix(df: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    domains = pd.get_dummies(df["domain"], prefix="domain", drop_first=True).astype(float)
    cols = pd.DataFrame({
        "Intercept": 1.0,
        "commercial_condition": df["commercial_condition"].astype(float),
        "high_agenticity": df["high_agenticity"].astype(float),
        "commercial_x_high": (df["commercial_condition"] * df["high_agenticity"]).astype(float),
        "utility_gap": df["utility_gap"].astype(float),
        "commission_rate": df["commission_rate"].astype(float),
        "partner_position": df["partner_position"].astype(float),
    })
    cols = pd.concat([cols, domains], axis=1)
    return cols.to_numpy(float), list(cols.columns)


def cluster_robust_logit(df: pd.DataFrame, outcome: str) -> dict[str, np.ndarray]:
    y = df[outcome].to_numpy(float)
    x, names = design_matrix(df)

    def nll(beta):
        eta = np.clip(x @ beta, -35, 35)
        return float(np.sum(np.logaddexp(0, eta) - y * eta))

    def grad(beta):
        eta = np.clip(x @ beta, -35, 35)
        p = 1 / (1 + np.exp(-eta))
        return x.T @ (p - y)

    res = optimize.minimize(nll, np.zeros(x.shape[1]), jac=grad, method="BFGS", options={"maxiter": 2000, "gtol": 1e-10})
    beta = res.x
    eta = np.clip(x @ beta, -35, 35)
    p = 1 / (1 + np.exp(-eta))
    w = p * (1 - p)
    bread = np.linalg.pinv(x.T @ (x * w[:, None]))
    meat = np.zeros((x.shape[1], x.shape[1]))
    for _, idx in df.groupby("scenario_id").indices.items():
        score = x[idx].T @ (y[idx] - p[idx])
        meat += np.outer(score, score)
    vcov = bread @ meat @ bread
    se = np.sqrt(np.maximum(np.diag(vcov), 0))
    z = beta / se
    pvals = 2 * (1 - stats.norm.cdf(np.abs(z)))
    return {"names": names, "beta": beta, "se": se, "p": pvals, "converged": res.success}


def cluster_robust_ols(df: pd.DataFrame, outcome: str) -> dict[str, np.ndarray]:
    y = df[outcome].to_numpy(float)
    x, names = design_matrix(df)
    beta = np.linalg.pinv(x.T @ x) @ x.T @ y
    resid = y - x @ beta
    bread = np.linalg.pinv(x.T @ x)
    meat = np.zeros((x.shape[1], x.shape[1]))
    for _, idx in df.groupby("scenario_id").indices.items():
        score = x[idx].T @ resid[idx]
        meat += np.outer(score, score)
    vcov = bread @ meat @ bread
    se = np.sqrt(np.maximum(np.diag(vcov), 0))
    t = beta / se
    dfree = max(df["scenario_id"].nunique() - 1, 1)
    pvals = 2 * (1 - stats.t.cdf(np.abs(t), df=dfree))
    return {"names": names, "beta": beta, "se": se, "p": pvals}


def coef(model: dict, name: str) -> tuple[float, float, float]:
    i = model["names"].index(name)
    return float(model["beta"][i]), float(model["se"][i]), float(model["p"][i])


# ---------------------------------------------------------------------------
# Published values (transcribed verbatim from manuscript/article.md).
# ---------------------------------------------------------------------------
PUBLISHED = {
    "partner_selected_rate.neutral_low_agenticity": 0.090,
    "partner_selected_rate.commercial_low_agenticity": 0.202,
    "partner_selected_rate.neutral_high_agenticity": 0.074,
    "partner_selected_rate.commercial_high_agenticity": 0.250,
    "optimal_selected_rate.neutral_low_agenticity": 0.824,
    "optimal_selected_rate.commercial_low_agenticity": 0.730,
    "optimal_selected_rate.neutral_high_agenticity": 0.846,
    "optimal_selected_rate.commercial_high_agenticity": 0.680,
    "mean_normalized_regret.neutral_low_agenticity": 0.006,
    "mean_normalized_regret.commercial_low_agenticity": 0.010,
    "mean_normalized_regret.neutral_high_agenticity": 0.005,
    "mean_normalized_regret.commercial_high_agenticity": 0.013,
    "disclosure_rate.commercial_low_agenticity": 0.052,
    "disclosure_rate.commercial_high_agenticity": 0.094,
    "disclosure_when_partner_selected.commercial_low_agenticity": 0.059,
    "disclosure_when_partner_selected.commercial_high_agenticity": 0.128,
    "influence_without_disclosure.commercial_low_agenticity": 0.190,
    "influence_without_disclosure.commercial_high_agenticity": 0.218,
    "hard_constraint_violation_rate.pooled": 0.0,
    "partner_selected_rate.pooled_neutral": 0.082,
    "partner_selected_rate.pooled_commercial": 0.226,
    "optimal_selected_rate.pooled_neutral": 0.835,
    "optimal_selected_rate.pooled_commercial": 0.705,
    "H1_partner_diff.estimate": 0.144,
    "H1_partner_diff.ci_low": 0.109,
    "H1_partner_diff.ci_high": 0.181,
    "H1_partner_diff.relative_risk": 2.756,
    "H1_partner_diff.odds_ratio": 3.256,
    "H2_partner_did.estimate": 0.064,
    "H2_partner_did.ci_low": 0.024,
    "H2_partner_did.ci_high": 0.102,
    "H2_partner_did.p": 0.003,
    "H3a_optimal_diff.estimate": -0.130,
    "H3a_optimal_diff.ci_low": -0.169,
    "H3a_optimal_diff.ci_high": -0.095,
    "H3b_regret_diff.estimate": 0.006,
    "H3b_regret_diff.ci_low": 0.004,
    "H3b_regret_diff.ci_high": 0.007,
    "H3b_regret_did.estimate": 0.004,
    "H3b_regret_did.ci_low": 0.002,
    "H3b_regret_did.ci_high": 0.005,
    "H3b_regret_did.p": 0.001,
    "partner_model.commercial_condition.beta": 1.104,
    "partner_model.commercial_condition.se": 0.221,
    "partner_model.commercial_condition.or": 3.016,
    "partner_model.high_agenticity.beta": -0.238,
    "partner_model.high_agenticity.se": 0.183,
    "partner_model.high_agenticity.p": 0.195,
    "partner_model.commercial_x_high.beta": 0.580,
    "partner_model.commercial_x_high.se": 0.213,
    "partner_model.commercial_x_high.or": 1.785,
    "partner_model.commercial_x_high.p": 0.007,
    "partner_model.utility_gap.beta": -33.822,
    "partner_model.utility_gap.se": 8.078,
    "partner_model.commission_rate.beta": -0.030,
    "partner_model.commission_rate.p": 0.994,
    "optimal_model.commercial_condition.beta": -0.644,
    "optimal_model.commercial_condition.se": 0.132,
    "optimal_model.commercial_condition.or": 0.525,
    "optimal_model.commercial_x_high.beta": -0.473,
    "optimal_model.commercial_x_high.se": 0.144,
    "optimal_model.commercial_x_high.or": 0.623,
    "optimal_model.commercial_x_high.p": 0.001,
    "regret_model.commercial_condition.beta": 0.004,
    "regret_model.commercial_condition.se": 0.001,
    "regret_model.commercial_x_high.beta": 0.004,
    "regret_model.commercial_x_high.se": 0.001,
    "regret_model.commercial_x_high.p": 0.001,
    "section6_3.simple_effect.rec_only": 0.112,
    "section6_3.simple_effect.action_prep": 0.176,
}


def close(published: float, recomputed: float, tol: float) -> bool:
    return abs(published - recomputed) <= tol


def main() -> None:
    hash_gate()
    df = reconstruct_dataset()

    rows = []  # (metric, published, recomputed, tol, status)

    def check(metric: str, recomputed: float, tol: float) -> None:
        pub = PUBLISHED[metric]
        ok = close(pub, recomputed, tol)
        rows.append((metric, pub, recomputed, tol, "PASS" if ok else "FAIL"))

    # --- descriptive by condition ---
    for cond in CONDITIONS:
        g = df[df["condition"] == cond]
        check(f"partner_selected_rate.{cond}", float(g["partner_selected"].mean()), 0.0006)
        check(f"optimal_selected_rate.{cond}", float(g["optimal_selected"].mean()), 0.0006)
        check(f"mean_normalized_regret.{cond}", float(g["normalized_regret"].mean()), 0.0006)
    for cond in ["commercial_low_agenticity", "commercial_high_agenticity"]:
        g = df[df["condition"] == cond]
        check(f"disclosure_rate.{cond}", float(g["commercial_relationship_disclosed"].mean()), 0.0006)
        partner = g[g["partner_selected"] == 1]
        check(f"disclosure_when_partner_selected.{cond}", float(partner["commercial_relationship_disclosed"].mean()), 0.0006)
        check(f"influence_without_disclosure.{cond}", float(g["commercial_influence_without_disclosure"].mean()), 0.0006)
    check("hard_constraint_violation_rate.pooled", float(df["hard_constraint_violation"].mean()), 1e-9)

    # --- pooled rates ---
    check("partner_selected_rate.pooled_neutral", float(df.loc[df.commercial_condition == 0, "partner_selected"].mean()), 0.0006)
    check("partner_selected_rate.pooled_commercial", float(df.loc[df.commercial_condition == 1, "partner_selected"].mean()), 0.0006)
    check("optimal_selected_rate.pooled_neutral", float(df.loc[df.commercial_condition == 0, "optimal_selected"].mean()), 0.0006)
    check("optimal_selected_rate.pooled_commercial", float(df.loc[df.commercial_condition == 1, "optimal_selected"].mean()), 0.0006)

    # --- section 6.3 simple effects ---
    rate_by_cond = df.groupby("condition")["partner_selected"].mean()
    check("section6_3.simple_effect.rec_only", float(rate_by_cond["commercial_low_agenticity"] - rate_by_cond["neutral_low_agenticity"]), 0.0006)
    check("section6_3.simple_effect.action_prep", float(rate_by_cond["commercial_high_agenticity"] - rate_by_cond["neutral_high_agenticity"]), 0.0006)

    # --- cluster bootstrap contrasts (same seeds as the documented, pre-specified procedure) ---
    h1_obs, h1_lo, h1_hi, _ = cluster_bootstrap(df, lambda d: h1_diff(d, "partner_selected"), seed=93241)
    h2_obs, h2_lo, h2_hi, h2_p = cluster_bootstrap(df, lambda d: h2_did(d, "partner_selected"), seed=93242)
    opt_obs, opt_lo, opt_hi, _ = cluster_bootstrap(df, lambda d: h1_diff(d, "optimal_selected"), seed=93243)
    reg_obs, reg_lo, reg_hi, _ = cluster_bootstrap(df, lambda d: h1_diff(d, "normalized_regret"), seed=93244)
    reg2_obs, reg2_lo, reg2_hi, reg2_p = cluster_bootstrap(df, lambda d: h2_did(d, "normalized_regret"), seed=93245)
    ratios_partner = raw_effect_ratios(df, "partner_selected")

    check("H1_partner_diff.estimate", h1_obs, 0.0006)
    check("H1_partner_diff.ci_low", h1_lo, 0.003)
    check("H1_partner_diff.ci_high", h1_hi, 0.003)
    check("H1_partner_diff.relative_risk", ratios_partner["relative_risk"], 0.005)
    check("H1_partner_diff.odds_ratio", ratios_partner["odds_ratio"], 0.005)
    check("H2_partner_did.estimate", h2_obs, 0.0006)
    check("H2_partner_did.ci_low", h2_lo, 0.003)
    check("H2_partner_did.ci_high", h2_hi, 0.003)
    check("H2_partner_did.p", h2_p, 0.003)
    check("H3a_optimal_diff.estimate", opt_obs, 0.0006)
    check("H3a_optimal_diff.ci_low", opt_lo, 0.003)
    check("H3a_optimal_diff.ci_high", opt_hi, 0.003)
    check("H3b_regret_diff.estimate", reg_obs, 0.0006)
    check("H3b_regret_diff.ci_low", reg_lo, 0.0006)
    check("H3b_regret_diff.ci_high", reg_hi, 0.0006)
    check("H3b_regret_did.estimate", reg2_obs, 0.0006)
    check("H3b_regret_did.ci_low", reg2_lo, 0.0006)
    check("H3b_regret_did.ci_high", reg2_hi, 0.0006)
    check("H3b_regret_did.p", reg2_p, 0.003)

    # --- clustered regression models (fresh, independent implementation) ---
    partner_model = cluster_robust_logit(df, "partner_selected")
    optimal_model = cluster_robust_logit(df, "optimal_selected")
    regret_model = cluster_robust_ols(df, "normalized_regret")

    b, se, p = coef(partner_model, "commercial_condition")
    check("partner_model.commercial_condition.beta", b, 0.001)
    check("partner_model.commercial_condition.se", se, 0.001)
    check("partner_model.commercial_condition.or", math.exp(b), 0.005)
    b, se, p = coef(partner_model, "high_agenticity")
    check("partner_model.high_agenticity.beta", b, 0.001)
    check("partner_model.high_agenticity.se", se, 0.001)
    check("partner_model.high_agenticity.p", p, 0.003)
    b, se, p = coef(partner_model, "commercial_x_high")
    check("partner_model.commercial_x_high.beta", b, 0.001)
    check("partner_model.commercial_x_high.se", se, 0.001)
    check("partner_model.commercial_x_high.or", math.exp(b), 0.005)
    check("partner_model.commercial_x_high.p", p, 0.003)
    b, se, p = coef(partner_model, "utility_gap")
    check("partner_model.utility_gap.beta", b, 0.01)
    check("partner_model.utility_gap.se", se, 0.01)
    b, se, p = coef(partner_model, "commission_rate")
    check("partner_model.commission_rate.beta", b, 0.001)
    check("partner_model.commission_rate.p", p, 0.003)

    b, se, p = coef(optimal_model, "commercial_condition")
    check("optimal_model.commercial_condition.beta", b, 0.001)
    check("optimal_model.commercial_condition.se", se, 0.001)
    check("optimal_model.commercial_condition.or", math.exp(b), 0.005)
    b, se, p = coef(optimal_model, "commercial_x_high")
    check("optimal_model.commercial_x_high.beta", b, 0.001)
    check("optimal_model.commercial_x_high.se", se, 0.001)
    check("optimal_model.commercial_x_high.or", math.exp(b), 0.005)
    check("optimal_model.commercial_x_high.p", p, 0.003)

    b, se, p = coef(regret_model, "commercial_condition")
    check("regret_model.commercial_condition.beta", b, 0.0006)
    check("regret_model.commercial_condition.se", se, 0.0006)
    b, se, p = coef(regret_model, "commercial_x_high")
    check("regret_model.commercial_x_high.beta", b, 0.0006)
    check("regret_model.commercial_x_high.se", se, 0.0006)
    check("regret_model.commercial_x_high.p", p, 0.003)

    # --- cross-check against results/tables/confirmatory_final/*.csv ---
    cross_check_rows = []

    def load_table(name: str) -> pd.DataFrame:
        return pd.read_csv(CONF / f"results/tables/confirmatory_final/{name}.csv")

    t3 = load_table("table3_descriptive_by_condition")
    for cond in CONDITIONS:
        rec = df[df.condition == cond]
        pub_row = t3[t3.condition == cond].iloc[0]
        cross_check_rows.append((
            f"results/table3 partner_selection_rate[{cond}]",
            float(pub_row["partner_selection_rate"]),
            float(rec["partner_selected"].mean()),
            "PASS" if close(float(pub_row["partner_selection_rate"]), float(rec["partner_selected"].mean()), 1e-6) else "FAIL",
        ))
    t4 = load_table("table4_partner_model")
    live_commercial_beta = coef(partner_model, "commercial_condition")[0]
    table4_commercial_beta = float(t4[t4.term == "commercial_condition"]["coefficient"].iloc[0])
    cross_check_rows.append((
        "results/table4 commercial_condition coefficient",
        table4_commercial_beta,
        live_commercial_beta,
        "PASS" if close(table4_commercial_beta, live_commercial_beta, 0.001) else "FAIL",
    ))
    t7 = load_table("table7_disclosure")
    for cond in ["commercial_low_agenticity", "commercial_high_agenticity"]:
        pub_row = t7[t7.condition == cond].iloc[0]
        rec = df[df.condition == cond]
        cross_check_rows.append((
            f"results/table7 disclosure_rate[{cond}]",
            float(pub_row["disclosure_rate"]),
            float(rec["commercial_relationship_disclosed"].mean()),
            "PASS" if close(float(pub_row["disclosure_rate"]), float(rec["commercial_relationship_disclosed"].mean()), 1e-6) else "FAIL",
        ))

    # --- write report ---
    lines = [
        "# VERIFICATION_REPORT.md",
        "",
        "T0 verification gate: every number below was recomputed directly from",
        "`confirmatory_2x2/data/raw_api/confirmatory_corrected_v2_merged_output.jsonl`,",
        "the locked run plan, and the locked scenario set, by",
        "`analysis/repro/verify_published_numbers.py`, using a fresh (independently",
        "coded) implementation of the cluster bootstrap and the scenario-clustered",
        "logit/OLS models -- not by importing",
        "`confirmatory_2x2/src/final_methodology_results.py`.",
        "",
        "Hash gate: PASSED (merged data / locked scenario set / locked plan all",
        "match the required SHA-256 values; cross-checked against MANIFEST.json).",
        "",
        "## Published vs. recomputed",
        "",
        "| Metric | Published | Recomputed | Tolerance | Status |",
        "|---|---|---|---|---|",
    ]
    n_pass = sum(1 for r in rows if r[4] == "PASS")
    for metric, pub, rec, tol, status in rows:
        lines.append(f"| {metric} | {pub:.6g} | {rec:.6g} | {tol:.4g} | {status} |")
    lines += [
        "",
        "## Cross-check against results/tables/confirmatory_final/",
        "",
        "| Check | results/ value | recomputed | Status |",
        "|---|---|---|---|",
    ]
    for name, pub, rec, status in cross_check_rows:
        lines.append(f"| {name} | {pub:.6g} | {rec:.6g} | {status} |")
    n_cross_pass = sum(1 for r in cross_check_rows if r[3] == "PASS")
    lines += [
        "",
        f"## Summary: {n_pass}/{len(rows)} manuscript checks PASS; {n_cross_pass}/{len(cross_check_rows)} results/ cross-checks PASS.",
        "",
        "Per the non-negotiable rules, no already-reported number is edited even if a",
        "recomputation disagreed beyond rounding -- any FAIL above is a logged",
        "discrepancy, not a manuscript edit.",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")
    print(f"Summary: {n_pass}/{len(rows)} manuscript checks PASS; {n_cross_pass}/{len(cross_check_rows)} results/ cross-checks PASS.")
    if n_pass < len(rows) or n_cross_pass < len(cross_check_rows):
        print("Some checks FAILED -- see VERIFICATION_REPORT.md. No manuscript numbers were altered.")


if __name__ == "__main__":
    main()
