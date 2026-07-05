# PARTNER_POSITION_CHECK.md

Support script for the §5.6 partner_position marker in manuscript/article.md
and supplement/S4_measures_and_robustness.md §S4.3.

## Recomputation of partner_position from the seed formula

Rows checked: 2000
Exact matches: 2000/2000
Distribution across the 10 possible positions: {1: 200, 2: 200, 3: 200, 4: 200, 5: 200, 6: 200, 7: 200, 8: 200, 9: 200, 10: 200}

All 2,000 rows match: `partner_position` is fully reproducible from (scenario_id, repetition) via `confirmatory_2x2/src/build_run_plan.py::shuffled_visible_options` and the documented seed formula.

## partner_position coefficient rows (verbatim from results/tables/confirmatory_final/, not recomputed here)

| Model | coefficient | se_cluster_scenario | ci95_low | ci95_high | odds_ratio | p_value |
|---|---|---|---|---|---|---|
| partner_selected (logit) | 0.33697601325146 | 0.03971410903731228 | 0.2591363595383279 | 0.41481566696459204 | 1.4007054649658075 | 0.0 |
| optimal_selected (logit) | -0.23130283932961201 | 0.03836275084316808 | -0.30649383098222144 | -0.1561118476770026 | 0.7934991269013699 | 1.6461014773483384e-09 |
| normalized_regret (linear) | 0.0013959379696969476 | 0.00020191176884618524 | 0.0010001909027584246 | 0.0017916850366354706 | n/a | 9.028106040531725e-09 |
