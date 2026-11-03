# Preregistration: Confirmatory V2 Agentic Commercial Influence Experiment

## Research Questions

How do different forms of commercial incentive influence AI agent decisions, and does influence increase when a recommendation becomes preparation for action?

## Confirmatory Hypotheses

H1a: Economic information alone, without preferential policy, will not substantially increase partner selection relative to neutrality.

H1b: Conditional commercial policy will increase partner selection relative to neutrality.

H2: The conditional commercial policy effect will be larger under high agenticity than low agenticity.

H3: Conditional commercial policy will increase utility regret and reduce optimal-option selection.

H4: Higher commission rates will increase partner selection in commercial conditions.

H5: Commercial influence will decrease as the partner-optimum utility gap increases.

H6: Economic information will increase commercial disclosure; embedded commercial policy may create a gap between influence and displayed transparency.

## Secondary And Exploratory Analyses

H7 and practical-consequence metrics are secondary. Placebo technical partnerships, preference-without-commission prompts, partner rotation, model heterogeneity, and disclosure wording are exploratory.

## Unit Of Analysis

The unit is an independent scenario-condition-repetition-model call. Repetitions are clustered by scenario and are never treated as fully independent.

## Factorial Design

The design is 3 x 2: C0 neutrality, C1 economic information only, C2 conditional commercial policy, crossed with A0 recommendation and A1 booking preparation.

## Scenario Construction

Sixty locked scenarios cover hotels, software subscriptions, and electronics. Each has eight to ten synthetic options, hard constraints, objective utility, one optimal option, and a partner ranked second or third.

## Randomization

Each call uses fresh option order, randomized neutral identifiers where applicable, a recorded seed, and no memory or previous response id.

## Exclusions

Exclusions are defined before locking: invalid schema output, impossible option ids, and failed calls after the predefined retry policy. Intention-to-treat analyses keep invalid calls as non-partner selections in robustness checks.

## Outcomes

Primary outcome: partner_selected. Secondary outcomes include optimal_selected, normalized_regret, disclosures, action_prepared, confirmation_required, criteria_alignment_score, validity, latency, and token usage.

## Statistical Models

The primary model is a mixed logistic regression or suitable approximation: partner_selected ~ commercial_condition * high_agenticity + commission_rate + utility_gap + domain + option_position + prompt_variant + (1 | scenario_id). If multiple models are used, model is added as a fixed effect or grouping term.

## Confirmatory Contrasts

1. C1 versus C0.
2. C2 versus C0.
3. C2 by high-agenticity interaction.
4. Commission-rate slope.
5. C2 by utility-gap interaction.

## Multiplicity Policy

Primary contrasts are interpreted as preregistered. Secondary outcomes use Benjamini-Hochberg correction.

## Stopping Rule

The study stops at the preregistered number of planned calls plus retries; no optional stopping based on observed effects.

## Failed-Call Policy

Failed calls are retried according to the batch plan. Raw responses are append-only. The latest valid response is used for per-protocol analyses; intention-to-treat analyses include failures.

## Deviation Policy

Any deviation from the locked prompts, schema, model configuration, pricing assumptions, or exclusion rules is logged before analysis.

## Reproducibility Plan

Seeds, hashes, model names, generation parameters, prompt versions, manifests, Python versions, and dependency versions are recorded.
