# Rapport de conception confirmatoire V2

## 1. Faiblesses du pilote

Le pilote a valide la faisabilite, mais il reste descriptif: cinq scenarios, vingt observations uniques, format de sortie confondu avec l'agenticite, instruction commerciale trop directe, taux de commission fixe et un seul domaine.

## 2. Corrections apportees

La V2 cree une arborescence autonome, conserve le pilote intact, verrouille un jeu confirmatoire hashe, controle le schema de sortie, diversifie les domaines, stratifie commissions et ecarts d'utilite, et integre des tests placebos et contrefactuels.

## 3. Nouveau plan 3 x 2

Les conditions commerciales sont C0 neutralite, C1 information economique seule, C2 politique commerciale conditionnelle. Elles sont croisees avec A0 recommandation et A1 preparation fictive d'action.

## 4. Information economique versus politique commerciale

C1 teste si la simple connaissance d'une commission modifie la decision alors que la neutralite est explicitement maintenue. C2 teste une politique conditionnelle, non obligatoire, qui autorise la priorite lorsque le partenaire reste proche.

## 5. Controle du format de sortie

Les six conditions utilisent le meme outil fictif `submit_agentic_decision`, le meme schema, le meme parser et les memes champs d'action.

## 6. Commissions et ecarts d'utilite

Les commissions couvrent 5%, 10% et 15%. Les ecarts d'utilite vises sont environ 2%, 5%, 8% et 12%.

## 7. Tests contrefactuels

La V2 prevoit rotation du partenaire, partenariat technique placebo, commission sans preference, preference sans commission, permutation d'ordre et identifiants neutres.

## 8. Domaines

Les scenarios couvrent hotels, logiciels professionnels en abonnement et produits electroniques.

## 9. Hypotheses

H1a-H6 sont confirmatoires. H7 et les analyses de generalisation multi-modeles sont secondaires ou exploratoires.

## 10. Plan statistique

Le modele principal est une regression logistique mixte ou approximation adaptee avec regroupement par scenario. Les analyses de robustesse incluent bootstrap groupe, permutation appariee, erreurs standards groupees, domaines, modeles, intention-to-treat et per-protocol.

## 11. Puissance

La simulation compare 1,200, 2,880, 3,600 et 3,840 observations sous effets prudents. Nombre de lignes simulees: 64.

## 12. Cout

Le plan recommande est estime a 10.97 USD avec marge de 20%, sous tarifs placeholders a verifier manuellement.

## 13. Risques restants

Les scenarios restent synthetiques, les resultats dependront des modeles et parametres reels, les disclosures textuels peuvent necessiter un codage manuel supplementaire, et la generalisation externe devra etre repliquee.

## 14. Recommandation finale

Utiliser le plan recommande: 60 scenarios x 6 conditions x 8 repetitions = 2,880 observations, avec etude principale sur un modele puis sous-echantillon multi-modeles de generalisation.
