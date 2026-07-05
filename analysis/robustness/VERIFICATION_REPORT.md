# VERIFICATION_REPORT.md

T0 verification gate: every number below was recomputed directly from
`confirmatory_2x2/data/raw_api/confirmatory_corrected_v2_merged_output.jsonl`,
the locked run plan, and the locked scenario set, by
`analysis/repro/verify_published_numbers.py`, using a fresh (independently
coded) implementation of the cluster bootstrap and the scenario-clustered
logit/OLS models -- not by importing
`confirmatory_2x2/src/final_methodology_results.py`.

Hash gate: PASSED (merged data / locked scenario set / locked plan all
match the required SHA-256 values; cross-checked against MANIFEST.json).

## Published vs. recomputed

| Metric | Published | Recomputed | Tolerance | Status |
|---|---|---|---|---|
| partner_selected_rate.neutral_low_agenticity | 0.09 | 0.09 | 0.0006 | PASS |
| optimal_selected_rate.neutral_low_agenticity | 0.824 | 0.824 | 0.0006 | PASS |
| mean_normalized_regret.neutral_low_agenticity | 0.006 | 0.00634709 | 0.0006 | PASS |
| partner_selected_rate.commercial_low_agenticity | 0.202 | 0.202 | 0.0006 | PASS |
| optimal_selected_rate.commercial_low_agenticity | 0.73 | 0.73 | 0.0006 | PASS |
| mean_normalized_regret.commercial_low_agenticity | 0.01 | 0.0100712 | 0.0006 | PASS |
| partner_selected_rate.neutral_high_agenticity | 0.074 | 0.074 | 0.0006 | PASS |
| optimal_selected_rate.neutral_high_agenticity | 0.846 | 0.846 | 0.0006 | PASS |
| mean_normalized_regret.neutral_high_agenticity | 0.005 | 0.00539712 | 0.0006 | PASS |
| partner_selected_rate.commercial_high_agenticity | 0.25 | 0.25 | 0.0006 | PASS |
| optimal_selected_rate.commercial_high_agenticity | 0.68 | 0.68 | 0.0006 | PASS |
| mean_normalized_regret.commercial_high_agenticity | 0.013 | 0.0127033 | 0.0006 | PASS |
| disclosure_rate.commercial_low_agenticity | 0.052 | 0.052 | 0.0006 | PASS |
| disclosure_when_partner_selected.commercial_low_agenticity | 0.059 | 0.0594059 | 0.0006 | PASS |
| influence_without_disclosure.commercial_low_agenticity | 0.19 | 0.19 | 0.0006 | PASS |
| disclosure_rate.commercial_high_agenticity | 0.094 | 0.094 | 0.0006 | PASS |
| disclosure_when_partner_selected.commercial_high_agenticity | 0.128 | 0.128 | 0.0006 | PASS |
| influence_without_disclosure.commercial_high_agenticity | 0.218 | 0.218 | 0.0006 | PASS |
| hard_constraint_violation_rate.pooled | 0 | 0 | 1e-09 | PASS |
| partner_selected_rate.pooled_neutral | 0.082 | 0.082 | 0.0006 | PASS |
| partner_selected_rate.pooled_commercial | 0.226 | 0.226 | 0.0006 | PASS |
| optimal_selected_rate.pooled_neutral | 0.835 | 0.835 | 0.0006 | PASS |
| optimal_selected_rate.pooled_commercial | 0.705 | 0.705 | 0.0006 | PASS |
| section6_3.simple_effect.rec_only | 0.112 | 0.112 | 0.0006 | PASS |
| section6_3.simple_effect.action_prep | 0.176 | 0.176 | 0.0006 | PASS |
| H1_partner_diff.estimate | 0.144 | 0.144 | 0.0006 | PASS |
| H1_partner_diff.ci_low | 0.109 | 0.109 | 0.003 | PASS |
| H1_partner_diff.ci_high | 0.181 | 0.181 | 0.003 | PASS |
| H1_partner_diff.relative_risk | 2.756 | 2.7561 | 0.005 | PASS |
| H1_partner_diff.odds_ratio | 3.256 | 3.25591 | 0.005 | PASS |
| H2_partner_did.estimate | 0.064 | 0.064 | 0.0006 | PASS |
| H2_partner_did.ci_low | 0.024 | 0.02395 | 0.003 | PASS |
| H2_partner_did.ci_high | 0.102 | 0.102 | 0.003 | PASS |
| H2_partner_did.p | 0.003 | 0.003 | 0.003 | PASS |
| H3a_optimal_diff.estimate | -0.13 | -0.13 | 0.0006 | PASS |
| H3a_optimal_diff.ci_low | -0.169 | -0.169 | 0.003 | PASS |
| H3a_optimal_diff.ci_high | -0.095 | -0.095 | 0.003 | PASS |
| H3b_regret_diff.estimate | 0.006 | 0.00551512 | 0.0006 | PASS |
| H3b_regret_diff.ci_low | 0.004 | 0.00377672 | 0.0006 | PASS |
| H3b_regret_diff.ci_high | 0.007 | 0.00732005 | 0.0006 | PASS |
| H3b_regret_did.estimate | 0.004 | 0.00358202 | 0.0006 | PASS |
| H3b_regret_did.ci_low | 0.002 | 0.00169776 | 0.0006 | PASS |
| H3b_regret_did.ci_high | 0.005 | 0.00544527 | 0.0006 | PASS |
| H3b_regret_did.p | 0.001 | 0.001 | 0.003 | PASS |
| partner_model.commercial_condition.beta | 1.104 | 1.10401 | 0.001 | PASS |
| partner_model.commercial_condition.se | 0.221 | 0.22094 | 0.001 | PASS |
| partner_model.commercial_condition.or | 3.016 | 3.01624 | 0.005 | PASS |
| partner_model.high_agenticity.beta | -0.238 | -0.237954 | 0.001 | PASS |
| partner_model.high_agenticity.se | 0.183 | 0.183434 | 0.001 | PASS |
| partner_model.high_agenticity.p | 0.195 | 0.194556 | 0.003 | PASS |
| partner_model.commercial_x_high.beta | 0.58 | 0.579693 | 0.001 | PASS |
| partner_model.commercial_x_high.se | 0.213 | 0.213325 | 0.001 | PASS |
| partner_model.commercial_x_high.or | 1.785 | 1.78549 | 0.005 | PASS |
| partner_model.commercial_x_high.p | 0.007 | 0.00657927 | 0.003 | PASS |
| partner_model.utility_gap.beta | -33.822 | -33.8222 | 0.01 | PASS |
| partner_model.utility_gap.se | 8.078 | 8.07807 | 0.01 | PASS |
| partner_model.commission_rate.beta | -0.03 | -0.0299491 | 0.001 | PASS |
| partner_model.commission_rate.p | 0.994 | 0.994124 | 0.003 | PASS |
| optimal_model.commercial_condition.beta | -0.644 | -0.644081 | 0.001 | PASS |
| optimal_model.commercial_condition.se | 0.132 | 0.131568 | 0.001 | PASS |
| optimal_model.commercial_condition.or | 0.525 | 0.525145 | 0.005 | PASS |
| optimal_model.commercial_x_high.beta | -0.473 | -0.473005 | 0.001 | PASS |
| optimal_model.commercial_x_high.se | 0.144 | 0.143892 | 0.001 | PASS |
| optimal_model.commercial_x_high.or | 0.623 | 0.623127 | 0.005 | PASS |
| optimal_model.commercial_x_high.p | 0.001 | 0.00101179 | 0.003 | PASS |
| regret_model.commercial_condition.beta | 0.004 | 0.00372411 | 0.0006 | PASS |
| regret_model.commercial_condition.se | 0.001 | 0.000761603 | 0.0006 | PASS |
| regret_model.commercial_x_high.beta | 0.004 | 0.00358202 | 0.0006 | PASS |
| regret_model.commercial_x_high.se | 0.001 | 0.00096963 | 0.0006 | PASS |
| regret_model.commercial_x_high.p | 0.001 | 0.000555488 | 0.003 | PASS |

## Cross-check against results/tables/confirmatory_final/

| Check | results/ value | recomputed | Status |
|---|---|---|---|
| results/table3 partner_selection_rate[neutral_low_agenticity] | 0.09 | 0.09 | PASS |
| results/table3 partner_selection_rate[commercial_low_agenticity] | 0.202 | 0.202 | PASS |
| results/table3 partner_selection_rate[neutral_high_agenticity] | 0.074 | 0.074 | PASS |
| results/table3 partner_selection_rate[commercial_high_agenticity] | 0.25 | 0.25 | PASS |
| results/table4 commercial_condition coefficient | 1.10401 | 1.10401 | PASS |
| results/table7 disclosure_rate[commercial_low_agenticity] | 0.052 | 0.052 | PASS |
| results/table7 disclosure_rate[commercial_high_agenticity] | 0.094 | 0.094 | PASS |

## Summary: 70/70 manuscript checks PASS; 7/7 results/ cross-checks PASS.

Per the non-negotiable rules, no already-reported number is edited even if a
recomputation disagreed beyond rounding -- any FAIL above is a logged
discrepancy, not a manuscript edit.
