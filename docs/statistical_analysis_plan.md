# Statistical analysis implementation plan

Primary model:

`partner_selected ~ commercial_condition * high_agenticity + utility_gap + commission_rate_in_commercial_condition + domain + partner_position + scenario fixed effects`

When mixed logistic regression is available, the scenario term should be specified as `(1 | scenario_id)`. The repository also prepares scenario fixed effects, scenario-clustered standard errors, and clustered bootstrap robustness.

H1 is the main commercial-condition effect. H2 is the commercial-condition by high-agenticity interaction. H3a repeats the model for `optimal_selected`. H3b uses `normalized_regret` with the same fixed effects. Secondary outcomes receive Benjamini-Hochberg correction.
