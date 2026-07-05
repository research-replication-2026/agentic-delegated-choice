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
