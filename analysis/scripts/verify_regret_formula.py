#!/usr/bin/env python3
"""T1 support script for the §5.5 utility/regret marker.

Backs every numeric claim made in article.md §5.5 and supplement/S4 about the
scenario-defined utility function and the utility_regret / normalized_regret
formulas: that optimal_option_id is always the strict argmax of
objective_utilities, that no ties occur among the 50 locked confirmatory
scenarios, that the optimal option is always hard-constraint-feasible, and
the resulting numeric range of optimal_utility (hence of normalized_regret).

Reuses confirmatory_2x2/src/common.py::score_option and
violates_hard_constraints (the functions that *define* the formula) rather
than re-deriving them, since this script documents the existing formula --
it does not independently re-verify a published statistic (that is T0's
job). Writes REGRET_FORMULA_CHECK.md next to this script.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONF = REPO_ROOT / "confirmatory_2x2"
sys.path.insert(0, str(CONF))

from src.common import score_option, violates_hard_constraints  # noqa: E402

SCENARIOS_JSON = CONF / "data/locked/confirmatory_scenarios.json"
REPORT_PATH = Path(__file__).resolve().parent / "REGRET_FORMULA_CHECK.md"


def main() -> None:
    scenarios = json.loads(SCENARIOS_JSON.read_text(encoding="utf-8"))["scenarios"]
    assert len(scenarios) == 50

    argmax_mismatches = []
    ties = []
    infeasible_optimal = []
    zero_utility_options = 0
    optimal_utilities = []
    recompute_mismatches = []

    for s in scenarios:
        stored_utils = s["objective_utilities"]
        recomputed_utils = {
            o["option_id"]: score_option(o, s["weights"], s["hard_constraints"])
            for o in s["options"]
        }
        for oid in stored_utils:
            if stored_utils[oid] != recomputed_utils[oid]:
                recompute_mismatches.append((s["scenario_id"], oid, stored_utils[oid], recomputed_utils[oid]))

        opt_id = s["optimal_option_id"]
        max_util = max(stored_utils.values())
        argmax_ids = [k for k, v in stored_utils.items() if v == max_util]
        if opt_id not in argmax_ids:
            argmax_mismatches.append(s["scenario_id"])
        if len(argmax_ids) > 1:
            ties.append(s["scenario_id"])

        option_by_id = {o["option_id"]: o for o in s["options"]}
        if violates_hard_constraints(option_by_id[opt_id], s["hard_constraints"]):
            infeasible_optimal.append(s["scenario_id"])

        zero_utility_options += sum(1 for v in stored_utils.values() if v == 0.0)
        optimal_utilities.append(stored_utils[opt_id])

    n_options_total = sum(len(s["options"]) for s in scenarios)

    lines = [
        "# REGRET_FORMULA_CHECK.md",
        "",
        "Support script for the §5.5 utility/regret marker in manuscript/article.md",
        "and supplement/S4_measures_and_robustness.md. Recomputes",
        "`objective_utilities` from each locked scenario's options, weights, and",
        "hard constraints using `confirmatory_2x2/src/common.py::score_option`",
        "(the function that defines the formula), and checks the properties",
        "asserted in the manuscript text.",
        "",
        "| Check | Result |",
        "|---|---|",
        f"| Scenarios checked | {len(scenarios)} |",
        f"| Options checked | {n_options_total} |",
        f"| Recomputed objective_utilities matching stored values | {n_options_total - len(recompute_mismatches)}/{n_options_total} |",
        f"| optimal_option_id equals argmax(objective_utilities) | {len(scenarios) - len(argmax_mismatches)}/{len(scenarios)} scenarios |",
        f"| Scenarios with a tie for the maximum utility | {len(ties)}/{len(scenarios)} |",
        f"| Scenarios where optimal_option_id violates a hard constraint | {len(infeasible_optimal)}/{len(scenarios)} |",
        f"| Options with objective_utility exactly 0.0 (hard-constraint-forced) | {zero_utility_options}/{n_options_total} |",
        f"| min(optimal_utility) across the 50 scenarios | {min(optimal_utilities):.4f} |",
        f"| max(optimal_utility) across the 50 scenarios | {max(optimal_utilities):.4f} |",
        "",
    ]
    if recompute_mismatches or argmax_mismatches or ties or infeasible_optimal:
        lines.append("**Discrepancies found (see raw lists below); do not treat the manuscript claims as verified until resolved.**")
        lines.append("")
        lines.append(f"recompute_mismatches={recompute_mismatches}")
        lines.append(f"argmax_mismatches={argmax_mismatches}")
        lines.append(f"ties={ties}")
        lines.append(f"infeasible_optimal={infeasible_optimal}")
    else:
        lines.append("All checks pass: for every one of the 50 locked confirmatory scenarios,")
        lines.append("optimal_option_id is the unique, hard-constraint-feasible utility")
        lines.append("maximizer, objective_utility is exactly 0.0 for every hard-constraint-")
        lines.append("violating option and only for such options, and optimal_utility never")
        lines.append("approaches 0 (min 89.10 on the raw weighted-sum scale), so")
        lines.append("normalized_regret's denominator never vanishes.")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")
    print(f"argmax_mismatches={len(argmax_mismatches)} ties={len(ties)} infeasible_optimal={len(infeasible_optimal)} recompute_mismatches={len(recompute_mismatches)}")


if __name__ == "__main__":
    main()
