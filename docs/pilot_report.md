# Pilot report

## 1. Objective
Empirically validate a small pilot for testing whether a commercial incentive shifts hotel recommendations by an AI agent.

## 2. Design
Factorial 2 x 2 design: neutral/commercial incentive crossed with low/high agenticity. Five synthetic scenarios produce 20 planned observations.

## 3. Scenarios
Five synthetic hotel-selection scenarios were generated with fixed seed 20260629. Each scenario includes eight fictional hotels, hard constraints, weighted objective utility, an independently selected optimal option, and a non-optimal partner option ranked second or third.

## 4. Model used
gpt-5.4-mini

## 5. Number of calls
Planned observations: 20. Successful API observations in processed data: 20.

## 6. Valid response rate
1.000

## 7. Descriptive results
                 condition  n_observations  partner_selection_rate  optimal_selection_rate  mean_regret  hard_constraint_violation_rate  mean_alternatives_presented  commercial_disclosure_rate  valid_response_rate  action_preparation_rate
commercial_high_agenticity               5                     1.0                     0.0     0.049927                             0.0                          1.0                         0.0                  1.0                      1.0
 commercial_low_agenticity               5                     0.8                     0.2     0.039018                             0.0                          2.8                         1.0                  1.0                      0.0
   neutral_high_agenticity               5                     0.4                     0.6     0.015949                             0.0                          1.0                         0.0                  1.0                      1.0
    neutral_low_agenticity               5                     0.4                     0.4     0.018807                             0.0                          2.2                         0.0                  1.0                      0.0

## 8. Initial elements on H1
Commercial minus neutral partner-selection rate: 0.5.

## 9. Initial elements on H2
Low-agenticity commercial effect: 0.4. High-agenticity commercial effect: 0.6.

## 10. Initial elements on H3
Mean normalized regret by condition is reported descriptively in the table. This pilot cannot confirm H3.

## 11. Observed anomalies
No anomaly recorded beyond the small pilot scale and any API/format errors listed in the processed dataset.

## 12. Structured output quality
Structured outputs were parsed deterministically from raw JSONL records. Tool calls, when present, were parsed separately.

## 13. Token cost estimate
Input tokens recorded: 26358. Output tokens recorded: 3052. This is a token-volume summary, not a monetary price estimate.

## 14. Recommendations before full experiment
Increase scenario count, lock the model, pre-register the analysis plan, inspect malformed outputs, and run a small calibration batch before any 2,000-call experiment.

## 15. Pilot limits
This pilot is a technical and methodological validation exercise. It is not the confirmatory experiment and should not be interpreted as providing definitive evidence for or against the hypotheses.
