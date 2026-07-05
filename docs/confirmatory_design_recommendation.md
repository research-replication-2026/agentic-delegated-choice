# Confirmatory Design Recommendation

The pilot shows a global commercial effect of 0.50, a low-agenticity effect of 0.40, a high-agenticity effect of 0.60, and a descriptive interaction of 0.20. These estimates are useful for design but should not be used as confirmatory power assumptions because small pilots often overestimate effects.

## Recommended Design

The recommended confirmatory design is 50 scenarios x 4 conditions x 10 repetitions = 2,000 observations. This design balances cost, stability, and the need to estimate the H2 interaction. A smaller 1,000-observation design may be feasible but is more vulnerable to scenario heterogeneity. A 3,000-observation design is preferable if costs allow.

## Simulation Summary

|   scenarios |   repetitions_per_cell |   observations |   assumed_main_effect |   simulated_power_approx |
|------------:|-----------------------:|---------------:|----------------------:|-------------------------:|
|          50 |                      5 |           1000 |                  0.1  |                    0.981 |
|          50 |                      5 |           1000 |                  0.15 |                    1     |
|          50 |                      5 |           1000 |                  0.2  |                    1     |
|          50 |                      5 |           1000 |                  0.3  |                    1     |
|          50 |                     10 |           2000 |                  0.1  |                    1     |
|          50 |                     10 |           2000 |                  0.15 |                    1     |
|          50 |                     10 |           2000 |                  0.2  |                    1     |
|          50 |                     10 |           2000 |                  0.3  |                    1     |
|          75 |                     10 |           3000 |                  0.1  |                    1     |
|          75 |                     10 |           3000 |                  0.15 |                    1     |
|          75 |                     10 |           3000 |                  0.2  |                    1     |
|          75 |                     10 |           3000 |                  0.3  |                    1     |

The simulation uses scenario-level variability, nested repetitions, a commercial main effect, and a larger commercial effect in high agenticity. It is intentionally approximate and should be refined during preregistration.

## Analysis Plan

Use a preregistered model with clustering or random effects by scenario, fixed effects for commercial incentive and agenticity, and their interaction. Report descriptive rates, paired scenario-level contrasts, mixed-effects logistic models for partner selection, and paired models for regret.
