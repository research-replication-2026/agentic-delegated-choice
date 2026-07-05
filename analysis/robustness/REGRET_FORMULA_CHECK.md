# REGRET_FORMULA_CHECK.md

Support script for the §5.5 utility/regret marker in manuscript/article.md
and supplement/S4_measures_and_robustness.md. Recomputes
`objective_utilities` from each locked scenario's options, weights, and
hard constraints using `confirmatory_2x2/src/common.py::score_option`
(the function that defines the formula), and checks the properties
asserted in the manuscript text.

| Check | Result |
|---|---|
| Scenarios checked | 50 |
| Options checked | 500 |
| Recomputed objective_utilities matching stored values | 500/500 |
| optimal_option_id equals argmax(objective_utilities) | 50/50 scenarios |
| Scenarios with a tie for the maximum utility | 0/50 |
| Scenarios where optimal_option_id violates a hard constraint | 0/50 |
| Options with objective_utility exactly 0.0 (hard-constraint-forced) | 12/500 |
| min(optimal_utility) across the 50 scenarios | 89.1010 |
| max(optimal_utility) across the 50 scenarios | 95.9674 |

All checks pass: for every one of the 50 locked confirmatory scenarios,
optimal_option_id is the unique, hard-constraint-feasible utility
maximizer, objective_utility is exactly 0.0 for every hard-constraint-
violating option and only for such options, and optimal_utility never
approaches 0 (min 89.10 on the raw weighted-sum scale), so
normalized_regret's denominator never vanishes.
