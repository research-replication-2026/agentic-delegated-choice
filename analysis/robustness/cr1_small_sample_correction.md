# CR1 small-sample-corrected cluster-robust inference

Cameron & Miller (2015) CR1 finite-sample correction applied to the
already-fit scenario-clustered models (50 clusters, N=2000): sandwich SEs
are scaled by sqrt(G/(G-1) x (N-1)/(N-K)) and referred to a t(G-1)
distribution rather than the normal used for the headline estimates. Beta
estimates are unchanged; only inferential scale changes.

| Model | Term | beta | CR1 SE | CR1 p | CR1 CI low | CR1 CI high | df |
|---|---|---|---|---|---|---|---|
| partner_selected | commercial_condition | 1.1040 | 0.2236 | 9.607e-06 | 0.6546 | 1.5534 | 49 |
| partner_selected | high_agenticity | -0.2380 | 0.1857 | 0.206 | -0.6111 | 0.1352 | 49 |
| partner_selected | commercial_x_high | 0.5797 | 0.2159 | 0.009877 | 0.1458 | 1.0136 | 49 |
| optimal_selected | commercial_condition | -0.6441 | 0.1332 | 1.352e-05 | -0.9117 | -0.3765 | 49 |
| optimal_selected | high_agenticity | 0.1824 | 0.1215 | 0.1397 | -0.0618 | 0.4266 | 49 |
| optimal_selected | commercial_x_high | -0.4730 | 0.1456 | 0.002103 | -0.7657 | -0.1803 | 49 |
| normalized_regret | commercial_condition | 0.0037 | 0.0008 | 1.378e-05 | 0.0022 | 0.0053 | 49 |
| normalized_regret | high_agenticity | -0.0009 | 0.0007 | 0.1682 | -0.0023 | 0.0004 | 49 |
| normalized_regret | commercial_x_high | 0.0036 | 0.0010 | 0.0006365 | 0.0016 | 0.0056 | 49 |

Correction factor c = G/(G-1) x (N-1)/(N-K): partner_selected=1.0245, optimal_selected=1.0245, normalized_regret=1.0245.

**Comparison to headline (normal-reference) cluster-robust inference:**
all three focal terms that were significant at p < .01 under the normal
reference remain significant at p < .01 under the CR1/t(49) correction
(verify by comparing to the p-values in Table 4 and Table 6 of the main text and analysis/repro/FULL_COEFFICIENT_TABLES.md).
