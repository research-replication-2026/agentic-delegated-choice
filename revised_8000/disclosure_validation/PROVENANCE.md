# Existing double coding and AI-assisted harmonization

The authors identify the two supplied coding series as initial human codings and state that subsequent AI-assisted harmonization had already been performed. This release does not create annotations or redo adjudication.

`coder_A.csv` and `coder_B.csv` are deidentified projections of the saved `Codage` worksheet of the two retained workbooks. `coder_final.csv` projects the saved `Controle_50` worksheet of `codage_50.xlsx`. Campaign, response ID, field, indicator and exact existing label are retained. No label normalization, imputation or replacement is performed. `control_contexts_50.json.gz` supplies archived original text, selected-option IDs, partner IDs and catalogue mappings for deterministic NLP verification. The 17 historical responses are control-only, excluded from main-experiment estimates.

| Original source | SHA-256 |
|---|---|
| Codage_independant_Codeur_A.xlsx | `5d060b1638411982a89f1f1e303f0eb35a3d5c3a7e6a9a15a2948c131962573f` |
| Codage_independant_Codeur_B.xlsx | `c5e9bb0e35f3b355b62bc983a380d35857acf9a631bc93f8f81090c44d38c152` |
| codage_50.xlsx | `a453e22032446e63127f9d8d86e46c7fb104d40a6c379e43b5871fef41423372` |

The initial files' local names do not contain the `(2)` suffix mentioned in the authors' instructions; no identity with an unavailable differently named copy is inferred. The two retained files have distinct content and eight actual label differences, not duplicated final labels. Their instructions prescribe independent coding without consulting the other coder or NLP outputs. Creator/editor properties do not authenticate two individuals or actual execution of blinding; they are not published. Internal creation/export timestamps cannot establish the full coding chronology.

Initial agreement is 392/400 = 98.0%. With four nominal categories, observed agreement is .98 and chance agreement from the observed marginals is .432075. Unweighted Cohen's κ is `(0.98 − 0.432075)/(1 − 0.432075) = 21917/22717 = 0.9647840824052472`. The 400 units are nested in 50 responses and combine distinct indicators, not 400 independent responses or a unidimensional scale.

The final record retains all 392 shared initial labels; four initial disagreements match A and four match B. Equality establishes that each final value can be traced to an initial value. It does not supply an item-level log explaining who or what selected it. Initial A–B agreement and final-record–NLP concordance (388/400, 97.0%) are separate comparisons. The initial and final–NLP disagreement unit keys are disjoint, although some response IDs occur in both sets.

Older local notes variously attributed coding to AI alone or described editorial rewriting. Those historical source files are preserved locally. This release reports the later author account—human double coding followed by AI-assisted harmonization—with its evidential limits. The archived notes are not treated as a new coding series or an independently authenticated adjudication log. Full before/after scientific labels, rather than personal workbook metadata or free-text comments, are published for verification.

The sample is targeted and not representative. Its parent frame has known development overlap. These comparisons do not establish population accuracy, sensitivity/specificity, consumer exposure or comprehension. Missing text remains not observable; uncertainty and nonobservability are categories, not recoded negatives or missing cells.
