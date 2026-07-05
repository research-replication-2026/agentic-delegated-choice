# Power analysis

The simulator uses a hierarchical data-generating process with scenario-level random baselines, repeated-call correlation, domain variability represented through scenario heterogeneity, invalid-response risk placeholders, main commercial effects, weaker agenticity interactions, commission variation, and utility-gap variation.

The pilot effect of +0.50 is deliberately not used for sizing. Candidate main effects are +0.10, +0.15, +0.20, and +0.30. Candidate high-agenticity interactions are +0.05, +0.075, +0.10, and +0.15.

## Key recommended-plan row

| scenarios | repetitions | observations | assumed_main_effect | assumed_interaction | power_main_approx | power_interaction_approx |
| --- | --- | --- | --- | --- | --- | --- |
| 60 | 8 | 2880 | 0.15 | 0.075 | 1.0 | 0.677 |

The recommended plan remains 60 scenarios x 6 conditions x 8 repetitions = 2,880 observations, because it balances cost, scenario diversity, and the ability to estimate H2 without defaulting to the largest plan.
