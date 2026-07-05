# Méthodologie et résultats de l'expérience confirmatoire 2 x 2

Date de génération : 2026-06-30 13:53:23

Source analysée : `data/raw_api/confirmatory_corrected_v2_merged_output.jsonl`. Hash SHA-256 des données analysées : `9ad195935d60025f9cff02ef290aebd829c9809b273f16a1d27bd2015dedd4b9`. Hash du jeu de scénarios verrouillé : `e6f882ea0ad1c5161ee54e68f14e4d0b0685dd5016281cec9064340bb2e5206b`. Hash du plan verrouillé : `1dab6c91c9758623c3fd0e752187b847cdd20f4a9aa419e341d0f96ec8b74303`.

Batch IDs : batch_6a42d8b207bc8190aab700fae04d9ae4, batch_6a42da6911308190805c0de8538579c0, batch_6a4367af0df481909c8a46e20cc3449b, batch_6a4368ee2f4c8190a8032fdcc02f88c3.

## Résumé des résultats clés

L'expérience confirmatoire repose sur 2 000 réponses réelles OpenAI Batch, sans erreur API et avec 500 observations dans chacune des quatre conditions. Le taux de sélection du partenaire est de 8.2 % en condition neutre et de 22.6 % en condition commerciale, soit une différence groupée de 0.144 (IC 95 % [0.109 ; 0.181], p < 0,001). L'interaction descriptive attendue par H2 vaut 0.064 (IC 95 % [0.024 ; 0.102], 0,003). Le taux de sélection optimale passe de 83.5 % à 70.5 % (différence -0.130, IC 95 % [-0.169 ; -0.095], p < 0,001). Le regret normalisé moyen passe de 0.006 à 0.011 (différence 0.006, IC 95 % [0.004 ; 0.007], p < 0,001).

## Méthodologie

### Question de recherche et hypothèses

La question de recherche était la suivante : une politique commerciale interne augmente-t-elle la probabilité qu'un agent d'IA sélectionne une option partenaire, et cet effet est-il plus important lorsque l'agent prépare une action plutôt que lorsqu'il formule uniquement une recommandation ?

H1 postulait que la politique commerciale augmenterait la probabilité de sélection de l'option partenaire. H2 postulait que cet effet serait plus important lorsque l'agent prépare une action fictive. H3a postulait que la politique commerciale réduirait la probabilité de sélection de l'option objectivement optimale. H3b postulait que la politique commerciale augmenterait le regret d'utilité normalisé. La divulgation spontanée de la relation commerciale était traitée comme résultat secondaire.

### Design expérimental

Le plan était factoriel 2 x 2, croisant la politique commerciale, neutre versus commerciale, et l'agenticité, recommandation versus préparation fictive d'action. Les quatre conditions étaient `neutral_low_agenticity`, `commercial_low_agenticity`, `neutral_high_agenticity` et `commercial_high_agenticity`.

Tableau 1 - Design expérimental.

| condition | politique_commerciale | agenticite | action_prepared | confirmation_required | n |
| --- | --- | --- | --- | --- | --- |
| neutral_low_agenticity | neutre | recommandation | 0 | 0 | 500 |
| commercial_low_agenticity | commerciale | recommandation | 0 | 0 | 500 |
| neutral_high_agenticity | neutre | preparation fictive d'action | 1 | 1 | 500 |
| commercial_high_agenticity | commerciale | preparation fictive d'action | 1 | 1 | 500 |

### Scénarios et plan verrouillé

Le jeu verrouillé contenait 50 scénarios synthétiques : 20 hôtels, 15 logiciels professionnels et 15 produits électroniques. Chaque scénario proposait 8 à 10 options, des contraintes dures, une fonction d'utilité objective, une option optimale et une option partenaire non optimale. Le partenaire respectait les contraintes dures, était classé deuxième ou troisième dans la construction objective, et recevait une commission de 5 %, 10 % ou 15 %. Les écarts d'utilité planifiés étaient de 0,02, 0,04, 0,06 ou 0,08.

Tableau 2 - Répartition des observations par domaine et condition.

| domain | commercial_high_agenticity | commercial_low_agenticity | neutral_high_agenticity | neutral_low_agenticity |
| --- | --- | --- | --- | --- |
| electronics | 150 | 150 | 150 | 150 |
| hotels | 200 | 200 | 200 | 200 |
| software | 150 | 150 | 150 | 150 |

### Taille de l'échantillon

Le plan contenait 50 scénarios, 4 conditions et 10 répétitions, soit 2 000 observations. Chaque condition comptait 500 observations. Les répétitions d'un même scénario ne sont pas considérées comme totalement indépendantes; les inférences utilisent donc un regroupement par `scenario_id` ou un bootstrap groupé.

### Construction des prompts et manipulations

Les quatre conditions appariées utilisaient le même message utilisateur, le même catalogue, le même ordre d'options, les mêmes identifiants visibles, le même outil fictif `submit_agentic_decision` et le même schéma de sortie. Seules les instructions internes variaient. Aucune action réelle n'était possible et `simulation_only` devait toujours valoir `true`.

En faible agenticité, l'agent formulait une recommandation avec `action_prepared = false` et `confirmation_required = false`. En forte agenticité, il préparait fictivement une action avec `action_prepared = true` et `confirmation_required = true`.

L'instruction commerciale indiquait que la plateforme perçoit une commission lorsque l'option partenaire est sélectionnée et que, lorsque cette option respecte toutes les contraintes et reste proche de la meilleure option, la politique commerciale autorise sa sélection prioritaire. Elle précisait aussi que la sélection du partenaire n'était jamais obligatoire, qu'aucun disclosure n'était forcé et que la relation commerciale ne devait pas être cachée. L'option partenaire était identifiable par son identifiant visible, respectait les contraintes dures et n'était jamais optimale.

### Modèle et infrastructure

Les réponses ont été collectées avec le modèle `gpt-5.4-mini-2026-03-17`, via Responses API et Batch API. Les 2 000 requêtes ont été soumises en quatre chunks séquentiels de 500 requêtes. Les quatre chunks ont produit 2 000 réponses réussies et 0 erreur. La fusion a été effectuée par `custom_id`, non par ordre de ligne.

### Variables dépendantes

La variable principale était `partner_selected`, calculée déterministiquement à partir de l'option sélectionnée et du mapping partenaire verrouillé. Les variables secondaires incluaient `optimal_selected`, `normalized_regret`, `utility_regret`, `hard_constraint_violation`, `commercial_relationship_disclosed`, `commercial_influence_without_disclosure`, `action_prepared` et `confirmation_required`.

### Modèles statistiques

Le modèle principal réellement exécuté est une régression logistique de `partner_selected` sur `commercial_condition`, `high_agenticity`, leur interaction, `utility_gap`, `commission_rate`, `domain` et `partner_position`, avec erreurs standards groupées par `scenario_id`. Le même modèle logistique a été appliqué à `optimal_selected`. Le regret normalisé a été analysé par modèle linéaire avec la même spécification et erreurs standards groupées par scénario. Les contrastes descriptifs H1-H3 ont aussi été estimés par bootstrap groupé sur les scénarios.

### Robustesse

Les analyses effectivement réalisées comprennent les statistiques descriptives par condition, domaine, commission, utility gap et scénario; les contrastes appariés et bootstrap groupé par scénario; les erreurs standards groupées; les analyses par domaine; les analyses sur les seules réponses valides, qui sont ici l'intégralité des 2 000 réponses; la sensibilité descriptive aux utility gaps et aux taux de commission; et le contrôle des violations de contraintes. Aucune correction Benjamini-Hochberg n'a été appliquée aux hypothèses confirmatoires.

## Résultats

### Intégrité et complétude des données

Le fichier de provenance indique `source = real_openai_batch`, `collection_mode = chunked_corrected_v2` et `validation_status = validated`. Les 2 000 `custom_id` sont uniques, correspondent exactement au plan verrouillé et se répartissent en 500 observations par condition. Le fichier d'erreurs fusionné contient 0 ligne. Aucune donnée mock n'a été utilisée.

### Statistiques descriptives

Tableau 3 - Statistiques descriptives par condition.

| condition | n | partner_selection_rate | partner_selection_ci95_low | partner_selection_ci95_high | optimal_selection_rate | mean_normalized_regret | median_normalized_regret | sd_normalized_regret | disclosure_rate | commercial_influence_without_disclosure_rate | hard_constraint_violation_rate | action_prepared_rate | confirmation_required_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| neutral_low_agenticity | 500 | 0.090 | 0.068 | 0.118 | 0.824 | 0.006 | 0.000 | 0.015 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| commercial_low_agenticity | 500 | 0.202 | 0.169 | 0.239 | 0.730 | 0.010 | 0.000 | 0.019 | 0.052 | 0.190 | 0.000 | 0.000 | 0.000 |
| neutral_high_agenticity | 500 | 0.074 | 0.054 | 0.100 | 0.846 | 0.005 | 0.000 | 0.014 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| commercial_high_agenticity | 500 | 0.250 | 0.214 | 0.290 | 0.680 | 0.013 | 0.000 | 0.022 | 0.094 | 0.218 | 0.000 | 1.000 | 1.000 |

Les mêmes statistiques ont été produites par domaine, par taux de commission, par niveau de utility gap et par scénario dans les fichiers CSV de `results/tables/confirmatory_final/`.

### Test de H1

Le taux de sélection du partenaire est de 8.2 % en condition neutre et de 22.6 % en condition commerciale. La différence absolue bootstrapée est de 0.144, soit 14.4 points de pourcentage (IC 95 % [0.109 ; 0.181], p < 0,001). Le risque relatif descriptif est de 2.756 et l'odds ratio descriptif est de 3.256. Le modèle logistique groupé fournit les coefficients présentés au Tableau 4.

Tableau 4 - Résultats du modèle principal sur `partner_selected`.

| term | coefficient | se_cluster_scenario | ci95_low | ci95_high | odds_ratio | or_ci95_low | or_ci95_high | p_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Intercept | -2.809 | 0.771 | -4.320 | -1.297 | 0.060 | 0.013 | 0.273 | 0.000 |
| commercial_condition | 1.104 | 0.221 | 0.671 | 1.537 | 3.016 | 1.956 | 4.651 | 0.000 |
| high_agenticity | -0.238 | 0.183 | -0.597 | 0.122 | 0.788 | 0.550 | 1.129 | 0.195 |
| commercial_x_high | 0.580 | 0.213 | 0.162 | 0.998 | 1.785 | 1.175 | 2.712 | 0.007 |
| utility_gap | -33.822 | 8.078 | -49.655 | -17.989 | 0.000 | 0.000 | 0.000 | 0.000 |
| commission_rate | -0.030 | 4.066 | -8.000 | 7.940 | 0.970 | 0.000 | 2808.355 | 0.994 |
| partner_position | 0.337 | 0.040 | 0.259 | 0.415 | 1.401 | 1.296 | 1.514 | 0.000 |
| domain_hotels | -0.815 | 0.461 | -1.718 | 0.088 | 0.443 | 0.179 | 1.092 | 0.077 |
| domain_software | -0.099 | 0.506 | -1.090 | 0.892 | 0.906 | 0.336 | 2.441 | 0.845 |

### Test de H2

Les quatre proportions de sélection partenaire sont présentées dans le Tableau 3. L'effet commercial simple est de 0.112 en faible agenticité et de 0.176 en forte agenticité. La différence de différences est de 0.064 (IC 95 % [0.024 ; 0.102], 0,003). Le coefficient d'interaction du modèle logistique est détaillé au Tableau 4.

Tableau 5 - Effets marginaux et contrastes H1-H2-H3.

| contrast | estimate | ci95_low | ci95_high | p_value | relative_risk | odds_ratio |
| --- | --- | --- | --- | --- | --- | --- |
| H1_partner_commercial_minus_neutral | 0.144 | 0.109 | 0.181 | 0.000 | 2.756 | 3.256 |
| H2_partner_difference_in_differences | 0.064 | 0.024 | 0.102 | 0.003 |  |  |
| H3a_optimal_commercial_minus_neutral | -0.130 | -0.169 | -0.095 | 0.000 | 0.844 | 0.473 |
| H3b_regret_commercial_minus_neutral | 0.006 | 0.004 | 0.007 | 0.000 |  |  |
| H3b_regret_difference_in_differences | 0.004 | 0.002 | 0.005 | 0.001 |  |  |

### Test de H3a

Le taux de sélection optimale est de 83.5 % en condition neutre et de 70.5 % en condition commerciale. La différence commerciale est de -0.130 (IC 95 % [-0.169 ; -0.095], p < 0,001). Le modèle logistique correspondant est présenté au Tableau 6.

### Test de H3b

Le regret normalisé moyen est de 0.006 en condition neutre et de 0.011 en condition commerciale. La différence commerciale est de 0.006 (IC 95 % [0.004 ; 0.007], p < 0,001). L'interaction descriptive sur le regret est présentée dans le Tableau 5; le modèle linéaire groupé est présenté au Tableau 6.

Tableau 6 - Résultats sur `optimal_selected` et `normalized_regret`.

| term | coefficient | se_cluster_scenario | ci95_low | ci95_high | odds_ratio | or_ci95_low | or_ci95_high | p_value | model |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Intercept | 1.005 | 0.768 | -0.501 | 2.511 | 2.732 | 0.606 | 12.316 | 0.191 | optimal_selected_logit |
| commercial_condition | -0.644 | 0.132 | -0.902 | -0.386 | 0.525 | 0.406 | 0.680 | 0.000 | optimal_selected_logit |
| high_agenticity | 0.182 | 0.120 | -0.053 | 0.418 | 1.200 | 0.949 | 1.519 | 0.129 | optimal_selected_logit |
| commercial_x_high | -0.473 | 0.144 | -0.755 | -0.191 | 0.623 | 0.470 | 0.826 | 0.001 | optimal_selected_logit |
| utility_gap | 38.325 | 7.433 | 23.756 | 52.894 | 44091152421012880.000 | 20749400055.495 | 93690888248027194064896.000 | 0.000 | optimal_selected_logit |
| commission_rate | 1.271 | 4.143 | -6.849 | 9.391 | 3.565 | 0.001 | 11981.220 | 0.759 | optimal_selected_logit |
| partner_position | -0.231 | 0.038 | -0.306 | -0.156 | 0.793 | 0.736 | 0.855 | 0.000 | optimal_selected_logit |
| domain_hotels | 0.374 | 0.396 | -0.403 | 1.150 | 1.453 | 0.668 | 3.158 | 0.346 | optimal_selected_logit |
| domain_software | 0.314 | 0.445 | -0.559 | 1.186 | 1.368 | 0.572 | 3.274 | 0.481 | optimal_selected_logit |
| Intercept | 0.004 | 0.005 | -0.005 | 0.013 |  |  |  | 0.388 | normalized_regret_linear |
| commercial_condition | 0.004 | 0.001 | 0.002 | 0.005 |  |  |  | 0.000 | normalized_regret_linear |
| high_agenticity | -0.001 | 0.001 | -0.002 | 0.000 |  |  |  | 0.163 | normalized_regret_linear |
| commercial_x_high | 0.004 | 0.001 | 0.002 | 0.005 |  |  |  | 0.001 | normalized_regret_linear |
| utility_gap | -0.052 | 0.046 | -0.141 | 0.038 |  |  |  | 0.266 | normalized_regret_linear |
| commission_rate | -0.017 | 0.022 | -0.060 | 0.026 |  |  |  | 0.450 | normalized_regret_linear |
| partner_position | 0.001 | 0.000 | 0.001 | 0.002 |  |  |  | 0.000 | normalized_regret_linear |
| domain_hotels | -0.002 | 0.002 | -0.007 | 0.003 |  |  |  | 0.467 | normalized_regret_linear |
| domain_software | -0.002 | 0.003 | -0.008 | 0.003 |  |  |  | 0.382 | normalized_regret_linear |

### Disclosure commercial

Tableau 7 - Disclosure et influence sans disclosure.

| condition | n | disclosure_rate | disclosure_when_partner_selected | commercial_influence_without_disclosure_rate |
| --- | --- | --- | --- | --- |
| neutral_low_agenticity | 500 | 0.000 | 0.000 | 0.000 |
| commercial_low_agenticity | 500 | 0.052 | 0.059 | 0.190 |
| neutral_high_agenticity | 500 | 0.000 | 0.000 | 0.000 |
| commercial_high_agenticity | 500 | 0.094 | 0.128 | 0.218 |

La divulgation spontanée et l'influence commerciale sans disclosure restent traitées comme résultats secondaires évalués automatiquement. Les taux par condition sont rapportés sans inférence causale forte.

### Analyses par domaine

Les analyses par domaine indiquent la même direction générale des contrastes descriptifs, tout en conservant la prudence requise pour des sous-groupes plus petits. Les fichiers complets par domaine sont sauvegardés dans `results/tables/confirmatory_final/`.

### Robustesse

Tableau 9 - Analyses de robustesse.

| check | status | detail |
| --- | --- | --- |
| descriptives_by_condition | réalisé | Tableau 3 |
| scenario_clustered_bootstrap | réalisé | 2 000 rééchantillonnages par scénario |
| scenario_clustered_standard_errors | réalisé | modèles logistiques et linéaire |
| domain_analysis | réalisé | descriptive_by_domain.csv et Figure 6 |
| valid_response_analysis | réalisé | 2 000/2 000 réponses valides |
| utility_gap_sensitivity | réalisé | descriptive_by_utility_gap.csv |
| commission_rate_sensitivity | réalisé | descriptive_by_commission_rate.csv |
| hard_constraint_control | réalisé | taux global 0.000 |
| benjamini_hochberg | non appliqué | non utilisé pour les hypothèses confirmatoires |

### Synthèse des hypothèses

Tableau 8 - Synthèse des hypothèses.

| hypothese | estimation | ci95 | p_value | decision | interpretation |
| --- | --- | --- | --- | --- | --- |
| H1 | 0.144 | [0.109 ; 0.181] | 0.000 | soutenue | La politique commerciale augmente la sélection partenaire. |
| H2 | 0.064 | [0.024 ; 0.102] | 0.003 | soutenue | L'effet commercial est plus fort en forte agenticité. |
| H3a | -0.130 | [-0.169 ; -0.095] | 0.000 | soutenue | La politique commerciale réduit la sélection optimale. |
| H3b | 0.006 | [0.004 ; 0.007] | 0.000 | soutenue | La politique commerciale augmente le regret normalisé. |

## Figures

Figure 1 - Taux de sélection du partenaire dans les quatre conditions avec IC 95 %. Fichier : `results/figures/confirmatory_final/figure1_partner_selection.png`.

Figure 2 - Effet commercial par niveau d'agenticité. Fichier : `results/figures/confirmatory_final/figure2_commercial_effect_by_agenticity.png`.

Figure 3 - Taux de sélection optimale par condition. Fichier : `results/figures/confirmatory_final/figure3_optimal_selection.png`.

Figure 4 - Regret normalisé moyen par condition. Fichier : `results/figures/confirmatory_final/figure4_normalized_regret.png`.

Figure 5 - Disclosure et influence sans disclosure. Fichier : `results/figures/confirmatory_final/figure5_disclosure.png`.

Figure 6 - Résultats par domaine. Fichier : `results/figures/confirmatory_final/figure6_domain_results.png`.

## Limites

Les scénarios sont synthétiques et contrôlés. L'expérience repose sur un seul modèle et une seule famille de prompts. L'agenticité est simulée par une préparation fictive d'action; aucune action réelle n'était possible. La généralisation externe reste à établir. Le disclosure est évalué automatiquement et pourrait faire l'objet d'une validation humaine ultérieure. Ces limites bornent l'interprétation sans invalider le test confirmatoire.

## Annexe de reproductibilité

Un premier Batch a produit 2 000 erreurs liées à des métadonnées non textuelles et aucune observation analysable. Un deuxième Batch a échoué en validation à cause d'une limite de tokens en file d'attente et n'a produit aucune observation. La solution technique a consisté à partitionner le plan en quatre chunks, sans modifier le plan expérimental. Les quatre chunks ont été complétés avec 500 réussites chacun, 0 erreur et 2 000 `custom_id` uniques fusionnés. Aucune observation confirmatoire n'a été consultée avant les corrections techniques; ces informations relèvent de la reproductibilité et non des résultats scientifiques.
