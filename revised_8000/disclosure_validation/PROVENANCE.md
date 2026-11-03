# Existing double coding and AI-assisted harmonization

The 50-response control underwent human double coding followed by AI-assisted harmonization. The two initial coding files, the 400 matched assessments and their agreement have been verified directly from the retained annotations. This release does not create annotations or redo harmonization.

`coder_A.csv` and `coder_B.csv` are deidentified projections of the saved `Codage` worksheet of the two retained workbooks. `coder_final.csv` projects the saved `Controle_50` worksheet of `codage_50.xlsx`. Campaign, response ID, field, indicator and exact existing label are retained. No label normalization, imputation or replacement is performed. `control_contexts_50.json.gz` supplies archived original text, selected-option IDs, partner IDs and catalogue mappings for deterministic NLP verification. The 17 historical responses are control-only, excluded from main-experiment estimates.

| Original source | SHA-256 |
|---|---|
| Codage_independant_Codeur_A.xlsx | `5d060b1638411982a89f1f1e303f0eb35a3d5c3a7e6a9a15a2948c131962573f` |
| Codage_independant_Codeur_B.xlsx | `c5e9bb0e35f3b355b62bc983a380d35857acf9a631bc93f8f81090c44d38c152` |
| codage_50.xlsx | `a453e22032446e63127f9d8d86e46c7fb104d40a6c379e43b5871fef41423372` |

The two initial files are distinct workbooks with eight actual label differences, not duplicated final labels. Response identifiers, original texts, selected-option IDs and field-by-indicator labels were aligned across both series and the final record. The shared coding instructions are retained with the source files. Personal workbook properties and comments are excluded from the public exports for anonymity; the source hashes identify the exact records used.

Initial agreement is 392/400 = 98.0%. With four nominal categories, observed agreement is .98 and chance agreement from the observed marginals is .432075. Unweighted Cohen's κ is `(0.98 − 0.432075)/(1 − 0.432075) = 21917/22717 = 0.9647840824052472`. The 400 units are nested in 50 responses and combine distinct indicators, not 400 independent responses or a unidimensional scale.

The final record retains all 392 shared initial labels; four initial disagreements match A and four match B. The check confirms that every final value matches at least one initial annotation. Initial A–B agreement and final-record–NLP concordance (388/400, 97.0%) are separate comparisons. The initial and final–NLP disagreement unit keys are disjoint, although some response IDs occur in both sets.

The initial series, harmonized annotations and NLP outputs are provided as distinct stages of the validation chain. The supplied labels permit the agreement counts and kappa to be reproduced directly. Historical local source files remain unchanged; the public scientific account uses the verified two-series comparison and the existing final harmonized record.

The sample is targeted and not representative. Its parent frame has known development overlap. These comparisons do not establish population accuracy, sensitivity/specificity, consumer exposure or comprehension. Missing text remains not observable; uncertainty and nonobservability are categories, not recoded negatives or missing cells.
