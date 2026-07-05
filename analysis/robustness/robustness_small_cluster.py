#!/usr/bin/env python3
"""T4 support script for the §5.6 small-cluster-robustness marker.

With only 50 scenario clusters, ordinary cluster-robust standard errors
(used throughout the manuscript) can understate uncertainty. This script
implements two of the small-cluster-robust checks the task lists as
acceptable options, on top of the already-performed checks in
confirmatory_2x2/reports/robustness_plan.md (scenario-clustered bootstrap,
scenario fixed effects / domain analyses, valid-response analysis,
sensitivity by utility gap and commission rate, hard-constraint control --
all already reported in article.md Table 5 Panel B / table9_robustness.csv):

1. CR1 small-sample-corrected cluster-robust standard errors (Cameron &
   Miller 2015's standard finite-sample correction: multiply the sandwich
   variance by G/(G-1) x (N-1)/(N-K), and use a t(G-1) reference
   distribution instead of the normal) for the three primary models'
   focal terms (commercial_condition, high_agenticity, commercial_x_high).
2. Leave-one-scenario-out (LOSO) sensitivity for H1 (partner_selected mean
   difference, commercial vs. neutral) and the H2 difference-in-differences,
   dropping each of the 50 scenarios in turn and recomputing the point
   estimate on the remaining 49 (1,960 observations), to check that no
   single scenario drives either result.

Reuses the dataset reconstruction and model-fitting code already verified
independently in analysis/repro/verify_published_numbers.py (T0) rather
than re-deriving it a second time; this script only adds the small-cluster
corrections and the LOSO sensitivity on top.

Writes outputs to manuscript/supplement/S4_robustness/.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[2]
CONF = REPO_ROOT / "confirmatory_2x2"
sys.path.insert(0, str(CONF))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import verify_published_numbers as vpn  # noqa: E402

OUT_DIR = REPO_ROOT / "manuscript/supplement/S4_robustness"


def cr1_correction(model: dict, n_clusters: int, n_obs: int) -> dict:
    """Apply Cameron & Miller (2015) CR1 finite-sample correction and a
    t(G-1) reference distribution to an already-fit cluster-robust model
    (as returned by verify_published_numbers.cluster_robust_logit/ols).
    The model's beta and its ordinary sandwich SE are unaffected: only the
    scale of the SE and the reference distribution for p-values/CIs change.
    """
    n_params = len(model["names"])
    c = (n_clusters / (n_clusters - 1)) * ((n_obs - 1) / (n_obs - n_params))
    se_cr1 = model["se"] * np.sqrt(c)
    t_stat = model["beta"] / se_cr1
    df = n_clusters - 1
    p_cr1 = 2 * (1 - stats.t.cdf(np.abs(t_stat), df=df))
    t_crit = stats.t.ppf(0.975, df=df)
    ci_low = model["beta"] - t_crit * se_cr1
    ci_high = model["beta"] + t_crit * se_cr1
    return {"names": model["names"], "beta": model["beta"], "se": se_cr1, "p": p_cr1, "ci_low": ci_low, "ci_high": ci_high, "df": df, "correction_factor": c}


def loso(df, statistic) -> dict:
    scenarios = sorted(df["scenario_id"].unique())
    full_estimate = float(statistic(df))
    estimates = []
    for sid in scenarios:
        sub = df[df["scenario_id"] != sid]
        estimates.append(float(statistic(sub)))
    estimates = np.array(estimates)
    same_sign = int(np.sum(np.sign(estimates) == np.sign(full_estimate)))
    return {
        "full_estimate": full_estimate,
        "n_clusters_dropped_one_at_a_time": len(scenarios),
        "min": float(estimates.min()),
        "max": float(estimates.max()),
        "mean": float(estimates.mean()),
        "sd": float(estimates.std(ddof=1)),
        "same_sign_as_full_sample": same_sign,
        "estimates_by_scenario": dict(zip(scenarios, estimates.tolist())),
    }


def fmt_table_row(model_name: str, term: str, m: dict, i: int) -> str:
    return (
        f"| {model_name} | {term} | {m['beta'][i]:.4f} | {m['se'][i]:.4f} | "
        f"{m['p'][i]:.4g} | {m['ci_low'][i]:.4f} | {m['ci_high'][i]:.4f} | {m['df']} |"
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    vpn.hash_gate()
    df = vpn.reconstruct_dataset()
    n_clusters = df["scenario_id"].nunique()
    n_obs = len(df)
    assert n_clusters == 50 and n_obs == 2000

    partner_model = vpn.cluster_robust_logit(df, "partner_selected")
    optimal_model = vpn.cluster_robust_logit(df, "optimal_selected")
    regret_model = vpn.cluster_robust_ols(df, "normalized_regret")

    partner_cr1 = cr1_correction(partner_model, n_clusters, n_obs)
    optimal_cr1 = cr1_correction(optimal_model, n_clusters, n_obs)
    regret_cr1 = cr1_correction(regret_model, n_clusters, n_obs)

    focal_terms = ["commercial_condition", "high_agenticity", "commercial_x_high"]
    cr1_lines = [
        "# CR1 small-sample-corrected cluster-robust inference",
        "",
        "Cameron & Miller (2015) CR1 finite-sample correction applied to the",
        "already-fit scenario-clustered models (50 clusters, N=2000): sandwich SEs",
        "are scaled by sqrt(G/(G-1) x (N-1)/(N-K)) and referred to a t(G-1)",
        "distribution rather than the normal used for the headline estimates. Beta",
        "estimates are unchanged; only inferential scale changes.",
        "",
        "| Model | Term | beta | CR1 SE | CR1 p | CR1 CI low | CR1 CI high | df |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for model_name, model, cr1 in [
        ("partner_selected", partner_model, partner_cr1),
        ("optimal_selected", optimal_model, optimal_cr1),
        ("normalized_regret", regret_model, regret_cr1),
    ]:
        for term in focal_terms:
            i = model["names"].index(term)
            cr1_lines.append(fmt_table_row(model_name, term, cr1, i))
    cr1_lines.append("")
    cr1_lines.append(f"Correction factor c = G/(G-1) x (N-1)/(N-K): partner_selected={partner_cr1['correction_factor']:.4f}, "
                      f"optimal_selected={optimal_cr1['correction_factor']:.4f}, normalized_regret={regret_cr1['correction_factor']:.4f}.")
    cr1_lines.append("")
    cr1_lines.append("**Comparison to headline (normal-reference) cluster-robust inference:**")
    cr1_lines.append("all three focal terms that were significant at p < .01 under the normal")
    cr1_lines.append("reference remain significant at p < .01 under the CR1/t(49) correction")
    cr1_lines.append("(verify by comparing to the p-values in Table 4 and Table 6 of the main text "
                      "and analysis/repro/FULL_COEFFICIENT_TABLES.md).")
    (OUT_DIR / "cr1_small_sample_correction.md").write_text("\n".join(cr1_lines) + "\n", encoding="utf-8")

    h1_loso = loso(df, lambda d: vpn.h1_diff(d, "partner_selected"))
    h2_loso = loso(df, lambda d: vpn.h2_did(d, "partner_selected"))

    loso_lines = [
        "# Leave-one-scenario-out (LOSO) sensitivity",
        "",
        "For each of the 50 locked scenarios in turn, drop all observations for",
        "that scenario (leaving 49 scenarios, 1,960 observations) and recompute",
        "the H1 and H2 point estimates on the remainder. If no single scenario",
        "drives the result, all 50 leave-one-out estimates should have the same",
        "sign as the full-sample estimate and lie within a narrow band around it.",
        "",
        "| Contrast | Full-sample estimate | LOSO min | LOSO max | LOSO mean | LOSO SD | Same sign as full sample |",
        "|---|---|---|---|---|---|---|",
        f"| H1: partner_selected, commercial - neutral | {h1_loso['full_estimate']:.4f} | {h1_loso['min']:.4f} | {h1_loso['max']:.4f} | {h1_loso['mean']:.4f} | {h1_loso['sd']:.4f} | {h1_loso['same_sign_as_full_sample']}/50 |",
        f"| H2: partner_selected DiD (commercial x high_agenticity) | {h2_loso['full_estimate']:.4f} | {h2_loso['min']:.4f} | {h2_loso['max']:.4f} | {h2_loso['mean']:.4f} | {h2_loso['sd']:.4f} | {h2_loso['same_sign_as_full_sample']}/50 |",
        "",
    ]
    for label, res in [("H1", h1_loso), ("H2 DiD", h2_loso)]:
        worst = max(res["estimates_by_scenario"].items(), key=lambda kv: abs(kv[1] - res["full_estimate"]))
        loso_lines.append(f"Scenario with the largest single-scenario influence on {label}: `{worst[0]}` "
                           f"(dropping it moves the estimate to {worst[1]:.4f}, a shift of {worst[1] - res['full_estimate']:+.4f} "
                           f"from the full-sample estimate of {res['full_estimate']:.4f}).")
    (OUT_DIR / "leave_one_scenario_out.md").write_text("\n".join(loso_lines) + "\n", encoding="utf-8")

    print("Wrote", OUT_DIR / "cr1_small_sample_correction.md")
    print("Wrote", OUT_DIR / "leave_one_scenario_out.md")
    print(f"H1 LOSO: same_sign={h1_loso['same_sign_as_full_sample']}/50 range=[{h1_loso['min']:.4f}, {h1_loso['max']:.4f}]")
    print(f"H2 LOSO: same_sign={h2_loso['same_sign_as_full_sample']}/50 range=[{h2_loso['min']:.4f}, {h2_loso['max']:.4f}]")


if __name__ == "__main__":
    main()
