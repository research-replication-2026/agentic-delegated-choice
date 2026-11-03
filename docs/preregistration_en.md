# Preregistration: Confirmatory 2x2 Agentic Commercial Policy Experiment

## Research Question

Does an internal commercial policy increase the probability that an AI agent selects a partner option, and is this effect stronger when the agent prepares a fictitious action rather than only making a recommendation?

## Hypotheses

H1: The commercial policy increases partner selection.

H2: The commercial-policy effect is larger under high agenticity than under low agenticity.

H3a: The commercial policy reduces objectively optimal selection.

H3b: The commercial policy increases normalized utility regret.

Spontaneous disclosure of the commission or partnership is a secondary outcome.

## Unit Of Analysis

The unit of analysis is one independent scenario-condition-repetition call. Calls are clustered by scenario.

## Factorial Design

The design is 2 x 2: neutral versus commercial policy, crossed with low versus high agenticity. The four conditions are neutral_low_agenticity, commercial_low_agenticity, neutral_high_agenticity, and commercial_high_agenticity.

## Scenario Construction

The locked set contains exactly 50 synthetic scenarios: 20 hotels, 15 professional software subscriptions, and 15 electronic products. Each scenario contains 8 to 10 options, hard constraints, two primary criteria, one or two secondary criteria, an objective utility function, one optimal option, one partner option, a commission rate, and a partner-optimum utility gap.

## Randomization And Locking

The full 2,000-observation run plan is generated before API calls. It randomizes option order and visible identifiers, records seeds, and balances partner position. Scenario and run-plan hashes are stored before real collection.

## Primary Outcome

The primary outcome is partner_selected, computed deterministically from selected_option_id and the locked partner mapping.

## Secondary Outcomes

Secondary outcomes are optimal_selected, selected_utility, optimal_utility, utility_regret, normalized_regret, hard_constraint_violation, partner_rank, alternatives presented, optimal presented, commercial disclosure, action fields, validity, latency, and token counts.

## Exclusion And Failed Calls

Raw API data are append-only. Each observation can have up to three technical attempts. The latest valid attempt is used for the main per-protocol analysis. Invalid responses are not automatically coded as partner_selected=0; error rates are reported by condition and sensitivity analyses are prepared.

## Statistical Models

The primary model is partner_selected ~ commercial_condition * high_agenticity + utility_gap + commission_rate_in_commercial_condition + domain + partner_position + (1 | scenario_id). If mixed logistic regression is unavailable, scenario fixed effects, clustered standard errors, and clustered bootstrap are used.

## Contrasts

H1 is the commercial-condition main effect. H2 is [(commercial_high - neutral_high) - (commercial_low - neutral_low)]. H3a repeats the model for optimal_selected. H3b models normalized_regret.

## Multiplicity

H1, H2, H3a, and H3b are confirmatory. Secondary outcomes use Benjamini-Hochberg correction.

## Stopping Rule

The study stops after the locked 2,000 observations plus preregistered technical retries.

## Deviation Policy

Any deviation from locked scenarios, run plan, schema, prompts, exclusion rules, or model configuration is logged before analysis.

## Reproducibility

Seeds, hashes, prompts, schema, code, model names, generation parameters, Python version, dependency versions, manifests, and raw append-only files are preserved.
