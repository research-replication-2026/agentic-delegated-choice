# Leave-one-scenario-out (LOSO) sensitivity

For each of the 50 locked scenarios in turn, drop all observations for
that scenario (leaving 49 scenarios, 1,960 observations) and recompute
the H1 and H2 point estimates on the remainder. If no single scenario
drives the result, all 50 leave-one-out estimates should have the same
sign as the full-sample estimate and lie within a narrow band around it.

| Contrast | Full-sample estimate | LOSO min | LOSO max | LOSO mean | LOSO SD | Same sign as full sample |
|---|---|---|---|---|---|---|
| H1: partner_selected, commercial - neutral | 0.1440 | 0.1357 | 0.1490 | 0.1440 | 0.0026 | 50/50 |
| H2: partner_selected DiD (commercial x high_agenticity) | 0.0640 | 0.0592 | 0.0776 | 0.0640 | 0.0030 | 50/50 |

Scenario with the largest single-scenario influence on H1: `CON_SFT_029` (dropping it moves the estimate to 0.1357, a shift of -0.0083 from the full-sample estimate of 0.1440).
Scenario with the largest single-scenario influence on H2 DiD: `CON_HOT_019` (dropping it moves the estimate to 0.0776, a shift of +0.0136 from the full-sample estimate of 0.0640).
