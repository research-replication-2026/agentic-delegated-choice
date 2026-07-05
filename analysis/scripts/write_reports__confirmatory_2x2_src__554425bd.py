from __future__ import annotations

import csv

from src.common import path, write_csv, write_docx, write_text, write_xlsx
from src.provenance import require_real_batch_data


HYPOTHESES = [
    {"hypothesis": "H1", "label": "Commercial influence", "confirmatory": "yes", "outcome": "partner_selected", "test": "commercial_condition main effect"},
    {"hypothesis": "H2", "label": "Agenticity moderation", "confirmatory": "yes", "outcome": "partner_selected", "test": "commercial_condition x high_agenticity"},
    {"hypothesis": "H3a", "label": "Optimal selection", "confirmatory": "yes", "outcome": "optimal_selected", "test": "commercial_condition main and interaction terms"},
    {"hypothesis": "H3b", "label": "Utility regret", "confirmatory": "yes", "outcome": "normalized_regret", "test": "commercial_condition main and interaction terms"},
    {"hypothesis": "Secondary", "label": "Spontaneous disclosure", "confirmatory": "no", "outcome": "commercial_relationship_disclosed", "test": "descriptive and secondary models"},
]


def read_first(rel: str) -> dict[str, str]:
    target = path(rel)
    if not target.exists():
        return {}
    rows = list(csv.DictReader(target.open("r", encoding="utf-8")))
    return rows[0] if rows else {}


def preregistration() -> str:
    return """
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
"""


def protocol_fr() -> str:
    return """
# Protocole francais: experience confirmatoire 2 x 2

## Question de recherche

Une politique commerciale interne augmente-t-elle la probabilite qu'un agent d'IA choisisse une option partenaire, et cet effet est-il plus fort lorsque l'agent prepare une action fictive plutot que lorsqu'il formule seulement une recommandation ?

## Plan experimental

Le plan est factoriel 2 x 2. Le premier facteur oppose neutralite et politique commerciale. Le second oppose faible agenticite et forte agenticite. Les quatre conditions sont neutral_low_agenticity, commercial_low_agenticity, neutral_high_agenticity et commercial_high_agenticity.

## Taille

Le plan contient exactement 50 scenarios, 4 conditions et 10 repetitions independantes par scenario et condition, soit 2 000 observations.

## Scenarios

Les scenarios verrouilles comprennent 20 hotels, 15 logiciels professionnels et 15 produits electroniques. Chaque scenario contient une option optimale et une option partenaire non optimale mais proche, avec un ecart d'utilite cible entre environ 2% et 8%.

## Sortie technique

Toutes les conditions utilisent le meme outil fictif `submit_agentic_decision` et le meme schema. Aucune reservation, aucun achat et aucune transaction reelle ne sont possibles.

## Analyse

L'analyse principale tient compte du regroupement par scenario. La variable principale `partner_selected` est calculee de maniere deterministe et non par un LLM.
"""


def design_report() -> str:
    cost = read_first("results/tables/cost_estimation.csv")
    return f"""
# Rapport de conception confirmatoire 2 x 2

## 1. Question de recherche

L'experience teste si une politique commerciale interne augmente la selection d'une option partenaire et si cet effet s'intensifie lorsque l'agent prepare une action fictive.

## 2. Plan 2 x 2

Le design croise politique commerciale, neutre ou commerciale, et agenticite, faible ou forte.

## 3. Quatre conditions

Les conditions sont neutral_low_agenticity, commercial_low_agenticity, neutral_high_agenticity et commercial_high_agenticity.

## 4. Cinquante scenarios

Le jeu verrouille contient 50 scenarios: 20 hotels, 15 logiciels professionnels et 15 produits electroniques. Chaque scenario contient 8 a 10 options synthetiques, une option optimale et une option partenaire.

## 5. Deux mille observations

Le plan confirmatoire contient 50 scenarios x 4 conditions x 10 repetitions = 2 000 observations, avec une cle stable scenario_id + condition + repetition.

## 6. Meme format technique

Les quatre conditions utilisent le meme outil fictif `submit_agentic_decision`, le meme schema, le meme parser et les memes variables de sortie. La seule difference d'agenticite est la preparation fictive ou non de l'action.

## 7. Hypotheses

H1 teste l'influence commerciale. H2 teste la moderation par l'agenticite. H3a teste la baisse de selection optimale. H3b teste la hausse du regret normalise.

## 8. Variables

La variable principale est `partner_selected`. Les variables secondaires incluent selection optimale, utilite, regret, violations de contraintes, alternatives, disclosure, validite, latence et tokens.

## 9. Analyse statistique

Le modele principal est une regression logistique avec regroupement par scenario ou une approximation par effets fixes de scenario, erreurs groupees et bootstrap groupe.

## 10. Puissance

La simulation hierarchique compare des effets commerciaux de +10, +15, +20 et +30 points, et des interactions de +5, +10 et +15 points. Si l'interaction +5 points est sous-puissante, le rapport de puissance le signale sans changer le plan.

## 11. Cout

L'estimation utilise les consommations du pilote. Le cout standard avec marge de 20% est estime a {cost.get('standard_cost_with_20pct_margin', 'NA')} USD; le cout Batch API avec marge est estime a {cost.get('batch_cost_with_20pct_margin', 'NA')} USD. Les tarifs doivent etre verifies manuellement.

## 12. Limites

Les domaines restent synthetiques, l'effet dependra du modele et des parametres reels, et les disclosures peuvent necessiter une validation humaine supplementaire.

## 13. Pourquoi ce design est robuste sans etre inutilement complexe

Le plan 2 x 2 isole directement l'effet commercial, controle le format de sortie, conserve une taille fixe de 2 000 observations, preserve le regroupement par scenario et evite d'ajouter des facteurs exploratoires qui dilueraient la puissance de H2.
"""


def main() -> None:
    require_real_batch_data()
    write_csv("reports/hypotheses_table.csv", HYPOTHESES)
    write_xlsx("reports/hypotheses_table.xlsx", HYPOTHESES)
    write_text("reports/preregistration_en.md", preregistration())
    write_text("reports/protocol_fr.md", protocol_fr())
    report = design_report()
    write_text("reports/confirmatory_2x2_design_report_fr.md", report)
    write_docx("reports/confirmatory_2x2_design_report_fr.docx", report)
    print("Reports written.")


if __name__ == "__main__":
    main()
