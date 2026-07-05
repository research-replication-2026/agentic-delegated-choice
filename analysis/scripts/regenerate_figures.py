#!/usr/bin/env python3
"""T9 support script: regenerate manuscript figures directly from the data.

Regenerates figs/fig2-fig5 (the four data-driven figures; fig1_chain.png is
a conceptual diagram of the delegation chain with no underlying dataset and
is intentionally left untouched) from the T0-verified reconstructed dataset
(analysis/repro/verify_published_numbers.py), and builds a new
fig6_forest_focal_estimates.png: a forest plot of the three primary
scenario-clustered models' focal terms (commercial_condition and
commercial_x_high), reusing T0's own model fits.

Safety rule: for fig2-fig5, the values driving each figure are compared to
the already-verified PUBLISHED values (T0) within the same tolerances used
there. A figure is only written over the existing file if all of its
underlying values match; on any mismatch, the script stops, logs the
discrepancy, and leaves the original image file untouched.

Writes:
- manuscript/figs/fig2_partner_selection.png (overwritten if verified)
- manuscript/figs/fig3_effect_by_proximity.png (overwritten if verified)
- manuscript/figs/fig4_optimal_selection.png (overwritten if verified)
- manuscript/figs/fig5_regret.png (overwritten if verified)
- manuscript/figs/fig6_forest_focal_estimates.png (new)
- analysis/repro/FIGURE_REGENERATION_REPORT.md
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
CONF = REPO_ROOT / "confirmatory_2x2"
FIGS_DIR = REPO_ROOT / "manuscript/figs"
sys.path.insert(0, str(CONF))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import verify_published_numbers as vpn  # noqa: E402

NEUTRAL_COLOR = "#8A8A8A"
COMMERCIAL_COLOR = "#B3403A"
EDGE_COLOR = "#333333"
plt.rcParams["font.family"] = "serif"
plt.rcParams["axes.edgecolor"] = EDGE_COLOR
plt.rcParams["axes.linewidth"] = 0.8

CONDITION_ORDER = ["neutral_low_agenticity", "commercial_low_agenticity", "neutral_high_agenticity", "commercial_high_agenticity"]


def report_lines(title: str) -> list[str]:
    return ["", f"## {title}", ""]


def main() -> None:
    log: list[str] = ["# FIGURE_REGENERATION_REPORT.md", "", "All values recomputed from the T0-verified reconstructed dataset "
                       "(`analysis/repro/verify_published_numbers.py::reconstruct_dataset`) and checked against the "
                       "already-verified PUBLISHED values before any figure file is overwritten.", ""]

    vpn.hash_gate()
    df = vpn.reconstruct_dataset()
    tol = 0.0006
    stopped = False

    # ---- fig2: partner-selection rate by condition, grouped by proximity ----
    log += report_lines("fig2_partner_selection.png")
    rates, los, his = {}, {}, {}
    for cond in CONDITION_ORDER:
        g = df[df.condition == cond]["partner_selected"]
        rate = float(g.mean())
        lo, hi = vpn.wilson_ci(int(g.sum()), len(g))
        rates[cond], los[cond], his[cond] = rate, lo, hi
        pub = vpn.PUBLISHED[f"partner_selected_rate.{cond}"]
        ok = abs(pub - rate) <= tol
        log.append(f"- {cond}: recomputed={rate:.4f}, published={pub:.4f}, {'PASS' if ok else 'FAIL'}")
        if not ok:
            stopped = True
    if not stopped:
        fig, ax = plt.subplots(figsize=(6.1, 3.5), dpi=200)
        groups = ["Recommendation-only\ncondition", "Action-preparation\ncondition"]
        x = np.arange(2)
        width = 0.32
        neutral_vals = [rates["neutral_low_agenticity"], rates["neutral_high_agenticity"]]
        commercial_vals = [rates["commercial_low_agenticity"], rates["commercial_high_agenticity"]]
        neutral_err = [[neutral_vals[i] - los[c] for i, c in enumerate(["neutral_low_agenticity", "neutral_high_agenticity"])],
                       [his[c] - neutral_vals[i] for i, c in enumerate(["neutral_low_agenticity", "neutral_high_agenticity"])]]
        commercial_err = [[commercial_vals[i] - los[c] for i, c in enumerate(["commercial_low_agenticity", "commercial_high_agenticity"])],
                          [his[c] - commercial_vals[i] for i, c in enumerate(["commercial_low_agenticity", "commercial_high_agenticity"])]]
        b1 = ax.bar(x - width / 2, neutral_vals, width, yerr=neutral_err, capsize=4, color=NEUTRAL_COLOR, edgecolor=EDGE_COLOR, label="Neutral policy")
        b2 = ax.bar(x + width / 2, commercial_vals, width, yerr=commercial_err, capsize=4, color=COMMERCIAL_COLOR, edgecolor=EDGE_COLOR, label="Commercial policy")
        for i, v in enumerate(neutral_vals):
            ax.text(x[i] - width / 2, his[["neutral_low_agenticity", "neutral_high_agenticity"][i]] + 0.012, f"{v*100:.1f}%", ha="center", va="bottom")
        for i, v in enumerate(commercial_vals):
            ax.text(x[i] + width / 2, his[["commercial_low_agenticity", "commercial_high_agenticity"][i]] + 0.012, f"{v*100:.1f}%", ha="center", va="bottom")
        ax.set_xticks(x)
        ax.set_xticklabels(groups)
        ax.set_ylabel("Partner-selection rate")
        ax.set_ylim(0, 0.35)
        ax.yaxis.set_major_formatter(lambda v, _: f"{v*100:.0f}%")
        ax.spines[["top", "right"]].set_visible(False)
        ax.legend(loc="upper left", frameon=False)
        fig.tight_layout()
        fig.savefig(FIGS_DIR / "fig2_partner_selection.png")
        plt.close(fig)
        log.append("WROTE fig2_partner_selection.png")
    else:
        log.append("STOPPED: fig2 not regenerated; original file retained.")

    # ---- fig3: commercial-policy effect by proximity (DiD) ----
    log += report_lines("fig3_effect_by_proximity.png")
    rate_by_cond = df.groupby("condition")["partner_selected"].mean()
    simple_low = float(rate_by_cond["commercial_low_agenticity"] - rate_by_cond["neutral_low_agenticity"])
    simple_high = float(rate_by_cond["commercial_high_agenticity"] - rate_by_cond["neutral_high_agenticity"])
    did_obs, did_lo, did_hi, did_p = vpn.cluster_bootstrap(df, lambda d: vpn.h2_did(d, "partner_selected"), seed=93242)
    checks = [
        ("section6_3.simple_effect.rec_only", simple_low),
        ("section6_3.simple_effect.action_prep", simple_high),
        ("H2_partner_did.estimate", did_obs),
    ]
    fig3_ok = True
    for key, val in checks:
        pub = vpn.PUBLISHED[key]
        ok = abs(pub - val) <= 0.003
        log.append(f"- {key}: recomputed={val:.4f}, published={pub:.4f}, {'PASS' if ok else 'FAIL'}")
        fig3_ok = fig3_ok and ok
    if fig3_ok:
        fig, ax = plt.subplots(figsize=(5.5, 3.3), dpi=200)
        xs = [0, 1]
        ys = [simple_low * 100, simple_high * 100]
        ax.plot(xs, ys, color="#2E4B6E", marker="o", markersize=9, linewidth=2, zorder=3)
        for xi, yi in zip(xs, ys):
            ax.text(xi, yi + 0.6, f"+{yi:.1f} pts", ha="center", va="bottom")
        ax.annotate("", xy=(1.18, ys[1]), xytext=(1.18, ys[0]), arrowprops=dict(arrowstyle="<->", color="black"))
        p_text = "< .001" if did_p < 0.001 else f"= {did_p:.3f}".replace("0.", ".")
        ax.text(1.25, (ys[0] + ys[1]) / 2, f"Difference-in-differences\n= {did_obs:.3f}\n95% CI [{did_lo:.3f}, {did_hi:.3f}]\np {p_text}", va="center")
        ax.set_xlim(-0.4, 2.3)
        ax.set_xticks(xs)
        ax.set_xticklabels(["Recommendation\nonly", "Action\npreparation"])
        ax.set_ylabel("Commercial-policy effect on\npartner selection (pct. points)")
        ax.set_ylim(8, 20)
        ax.spines[["top", "right"]].set_visible(False)
        fig.tight_layout()
        fig.savefig(FIGS_DIR / "fig3_effect_by_proximity.png")
        plt.close(fig)
        log.append("WROTE fig3_effect_by_proximity.png")
    else:
        log.append("STOPPED: fig3 not regenerated; original file retained.")
        stopped = True

    # ---- fig4: optimal-selection rate by condition ----
    log += report_lines("fig4_optimal_selection.png")
    opt_rates = {}
    fig4_ok = True
    for cond in CONDITION_ORDER:
        g = df[df.condition == cond]["optimal_selected"]
        rate = float(g.mean())
        opt_rates[cond] = rate
        pub = vpn.PUBLISHED[f"optimal_selected_rate.{cond}"]
        ok = abs(pub - rate) <= tol
        log.append(f"- {cond}: recomputed={rate:.4f}, published={pub:.4f}, {'PASS' if ok else 'FAIL'}")
        fig4_ok = fig4_ok and ok
    if fig4_ok:
        fig, ax = plt.subplots(figsize=(6.1, 3.3), dpi=200)
        x = np.arange(2)
        width = 0.32
        neutral_vals = [opt_rates["neutral_low_agenticity"], opt_rates["neutral_high_agenticity"]]
        commercial_vals = [opt_rates["commercial_low_agenticity"], opt_rates["commercial_high_agenticity"]]
        ax.bar(x - width / 2, neutral_vals, width, color=NEUTRAL_COLOR, edgecolor=EDGE_COLOR, label="Neutral policy")
        ax.bar(x + width / 2, commercial_vals, width, color=COMMERCIAL_COLOR, edgecolor=EDGE_COLOR, label="Commercial policy")
        for i, v in enumerate(neutral_vals):
            ax.text(x[i] - width / 2, v + 0.015, f"{v*100:.1f}%", ha="center", va="bottom")
        for i, v in enumerate(commercial_vals):
            ax.text(x[i] + width / 2, v + 0.015, f"{v*100:.1f}%", ha="center", va="bottom")
        ax.set_xticks(x)
        ax.set_xticklabels(["Recommendation-only\ncondition", "Action-preparation\ncondition"])
        ax.set_ylabel("Scenario-defined optimal-selection rate")
        ax.set_ylim(0, 1.0)
        ax.yaxis.set_major_formatter(lambda v, _: f"{v*100:.0f}%")
        ax.spines[["top", "right"]].set_visible(False)
        ax.legend(loc="lower right", frameon=False)
        fig.tight_layout()
        fig.savefig(FIGS_DIR / "fig4_optimal_selection.png")
        plt.close(fig)
        log.append("WROTE fig4_optimal_selection.png")
    else:
        log.append("STOPPED: fig4 not regenerated; original file retained.")
        stopped = True

    # ---- fig5: mean normalized regret by condition ----
    log += report_lines("fig5_regret.png")
    reg_means = {}
    fig5_ok = True
    for cond in CONDITION_ORDER:
        g = df[df.condition == cond]["normalized_regret"]
        val = float(g.mean())
        reg_means[cond] = val
        pub = vpn.PUBLISHED[f"mean_normalized_regret.{cond}"]
        ok = abs(pub - val) <= tol
        log.append(f"- {cond}: recomputed={val:.4f}, published={pub:.4f}, {'PASS' if ok else 'FAIL'}")
        fig5_ok = fig5_ok and ok
    if fig5_ok:
        fig, ax = plt.subplots(figsize=(6.1, 3.3), dpi=200)
        x = np.arange(2)
        width = 0.32
        neutral_vals = [reg_means["neutral_low_agenticity"], reg_means["neutral_high_agenticity"]]
        commercial_vals = [reg_means["commercial_low_agenticity"], reg_means["commercial_high_agenticity"]]
        ax.bar(x - width / 2, neutral_vals, width, color=NEUTRAL_COLOR, edgecolor=EDGE_COLOR, label="Neutral policy")
        ax.bar(x + width / 2, commercial_vals, width, color=COMMERCIAL_COLOR, edgecolor=EDGE_COLOR, label="Commercial policy")
        for i, v in enumerate(neutral_vals):
            ax.text(x[i] - width / 2, v + 0.0003, f"{v:.3f}", ha="center", va="bottom")
        for i, v in enumerate(commercial_vals):
            ax.text(x[i] + width / 2, v + 0.0003, f"{v:.3f}", ha="center", va="bottom")
        ax.set_xticks(x)
        ax.set_xticklabels(["Recommendation-only\ncondition", "Action-preparation\ncondition"])
        ax.set_ylabel("Mean normalized regret")
        ax.set_ylim(0, 0.016)
        ax.spines[["top", "right"]].set_visible(False)
        ax.legend(loc="upper left", frameon=False)
        fig.tight_layout()
        fig.savefig(FIGS_DIR / "fig5_regret.png")
        plt.close(fig)
        log.append("WROTE fig5_regret.png")
    else:
        log.append("STOPPED: fig5 not regenerated; original file retained.")
        stopped = True

    # ---- fig6 (new): forest plot of the three models' focal terms ----
    log += report_lines("fig6_forest_focal_estimates.png (new)")
    partner_model = vpn.cluster_robust_logit(df, "partner_selected")
    optimal_model = vpn.cluster_robust_logit(df, "optimal_selected")
    regret_model = vpn.cluster_robust_ols(df, "normalized_regret")

    def or_ci(model, term):
        b, se, _ = vpn.coef(model, term)
        return np.exp(b), np.exp(b - 1.96 * se), np.exp(b + 1.96 * se)

    def lin_ci(model, term):
        b, se, _ = vpn.coef(model, term)
        return b, b - 1.96 * se, b + 1.96 * se

    or_rows = [
        ("Partner selected —\ncommercial policy", or_ci(partner_model, "commercial_condition")),
        ("Partner selected —\ncommercial × action-prep.", or_ci(partner_model, "commercial_x_high")),
        ("Optimal selected —\ncommercial policy", or_ci(optimal_model, "commercial_condition")),
        ("Optimal selected —\ncommercial × action-prep.", or_ci(optimal_model, "commercial_x_high")),
    ]
    lin_rows = [
        ("Normalized regret —\ncommercial policy", lin_ci(regret_model, "commercial_condition")),
        ("Normalized regret —\ncommercial × action-prep.", lin_ci(regret_model, "commercial_x_high")),
    ]
    log.append(f"OR rows: {[(n, tuple(round(v, 3) for v in vals)) for n, vals in or_rows]}")
    log.append(f"Linear rows: {[(n, tuple(round(v, 4) for v in vals)) for n, vals in lin_rows]}")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.2), dpi=200)
    y1 = np.arange(len(or_rows))[::-1]
    for yi, (name, (est, lo, hi)) in zip(y1, or_rows):
        ax1.plot([lo, hi], [yi, yi], color=EDGE_COLOR, linewidth=1.4, zorder=2)
        ax1.plot(est, yi, "o", color=COMMERCIAL_COLOR, markersize=8, zorder=3)
    ax1.axvline(1.0, color="#999999", linewidth=1, linestyle="--", zorder=1)
    ax1.set_xscale("log")
    all_or_vals = [v for _, vals in or_rows for v in vals]
    tick_candidates = [0.25, 0.5, 1, 2, 4, 8]
    ticks = [t for t in tick_candidates if min(all_or_vals) * 0.9 <= t <= max(all_or_vals) * 1.1]
    ax1.set_xticks(ticks)
    ax1.set_xticklabels([str(t) for t in ticks])
    ax1.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax1.set_yticks(y1)
    ax1.set_yticklabels([n for n, _ in or_rows])
    ax1.set_xlabel("Odds ratio (log scale), 95% scenario-clustered CI")
    ax1.set_title("Logistic models (partner_selected, optimal_selected)")
    ax1.spines[["top", "right"]].set_visible(False)

    y2 = np.arange(len(lin_rows))[::-1]
    for yi, (name, (est, lo, hi)) in zip(y2, lin_rows):
        ax2.plot([lo, hi], [yi, yi], color=EDGE_COLOR, linewidth=1.4, zorder=2)
        ax2.plot(est, yi, "o", color=COMMERCIAL_COLOR, markersize=8, zorder=3)
    ax2.axvline(0.0, color="#999999", linewidth=1, linestyle="--", zorder=1)
    ax2.set_yticks(y2)
    ax2.set_yticklabels([n for n, _ in lin_rows])
    ax2.set_xlabel("Coefficient (normalized-regret units),\n95% scenario-clustered CI")
    ax2.set_title("Linear model (normalized_regret)")
    ax2.spines[["top", "right"]].set_visible(False)

    fig.tight_layout()
    fig.savefig(FIGS_DIR / "fig6_forest_focal_estimates.png")
    plt.close(fig)
    log.append("WROTE fig6_forest_focal_estimates.png")

    (Path(__file__).resolve().parent / "FIGURE_REGENERATION_REPORT.md").write_text("\n".join(log) + "\n", encoding="utf-8")
    print("\n".join(log))
    if stopped:
        print("\nONE OR MORE FIGURES FAILED VERIFICATION -- see FIGURE_REGENERATION_REPORT.md")
        sys.exit(1)


if __name__ == "__main__":
    main()
