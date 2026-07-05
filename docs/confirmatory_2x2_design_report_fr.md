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

L'estimation utilise les consommations du pilote. Le cout standard avec marge de 20% est estime a 7.62 USD; le cout Batch API avec marge est estime a 3.81 USD. Les tarifs doivent etre verifies manuellement.

## 12. Limites

Les domaines restent synthetiques, l'effet dependra du modele et des parametres reels, et les disclosures peuvent necessiter une validation humaine supplementaire.

## 13. Pourquoi ce design est robuste sans etre inutilement complexe

Le plan 2 x 2 isole directement l'effet commercial, controle le format de sortie, conserve une taille fixe de 2 000 observations, preserve le regroupement par scenario et evite d'ajouter des facteurs exploratoires qui dilueraient la puissance de H2.
