# Revised Electronic Markets study: 8,000 archived responses

**Who decides when the agent chooses? Platform commercial instructions in delegated selection**

This is the revised study's analytical replication package. It is distinct from the earlier 2 × 2 experiment retained elsewhere in the repository. It reconstructs outcomes from archived raw responses and exact submitted requests; it does not generate new model responses.

## Design and implemented systems

The design contains 50 synthetic scenarios (20 hotels, 15 software, 15 electronics), two implementations, four policies, two simulated tasks and ten repetitions: **8,000 assignments**. GPT used the archived model identifier `gpt-5.4-mini-2026-03-17`, temperature 1, top_p .98, reasoning effort `none`, and max_output_tokens 1024. Claude used `claude-haiku-5-5`, max_tokens 1024 and forced tool use; temperature and top_p were not supplied in those requests. Provider/interface/configuration differences are bundled, not separately randomized.

The four policies are N (explicit neutrality), S (silence), I (commission information), and C (the same commission information plus conditional commercial priority). The two tasks are recommendation and simulated action preparation with confirmation. Neither executes a real transaction. Commissions vary across scenarios (5%, 10%, 15%); the exact visible partner IDs, rates, catalogue order and wording are present in every request archive.

**Authoritative instructions are the archived request payloads**, not a paraphrase or a template from the legacy experiment. `experimental_materials/exact_instruction_examples.json` gives eight actual GPT examples (policy × task); the 4,000 corresponding Claude stimuli have exactly matching system/user/schema content. All 8,000 full requests, including all substitutions, schemas, tools and transmitted settings, are in `experimental_materials/requests/`. Gzip compression is lossless and deterministic; uncompressed SHA-256 values match source archives. The executed French C instruction includes the original unusual non-obligation wording; it has not been retrospectively rewritten.

## Reproduce offline

Python 3.9 was used for verification. Install the pinned analytical dependencies in an isolated environment, then run from the repository root:

```bash
python -m venv .venv-replication
. .venv-replication/bin/activate
python -m pip install -r revised_8000/analysis/requirements.txt
python -B revised_8000/analysis/reproduce.py
python -B revised_8000/analysis/reproduce_mechanisms.py
python -B revised_8000/analysis/check_release.py
```

Dependency installation requires a package source; both scientific reproduction commands explicitly block network sockets and make no model calls. No API keys, provider account, SQLite ledger, workstation-specific path or private source tree is needed. Outputs are written only to `results/reproduced/`. The second command executes the unchanged archived exploratory script in a disposable compatibility tree built entirely from this checkout and the first command's freshly reconstructed scores.

`experimental_materials/source_generation/` preserves historical preparation/generation code as provenance. Those scripts are not the portable reproduction entrypoints and are not used to construct approximate replacement instructions. One personal path in a historical manuscript-integrity guard is redacted, with the original source hash and transformation recorded. Original experimental strings are unchanged.

## Data, outputs and evidence chain

| Location | Contents |
|---|---|
| experimental_materials/requests/ | Four GPT and four Claude exact request batches, 1,000 requests each |
| experimental_materials/ | Executed schema, dated local protocol, exact instruction examples and archival source-generation code |
| data/scenarios.json | 50 synthetic catalogues, constraints, private utility scores and benchmark targets |
| data/assignments_* | Synthetic assignment IDs and visible-to-canonical mappings; these are not participant identities |
| data/raw/ | Eight exact archived provider response envelopes, 4,000 per implementation |
| data/processed/ | Existing analysis-ready rows and frozen NLP reference classifications, with local source paths excluded |
| analysis/ | Portable adapters and unchanged original scoring/inference/exploratory implementations |
| disclosure_validation/ | Frozen NLP v2.2.0 rules, codebook, three deidentified coding series, and 50 existing control contexts |
| results/reference/ | Archived scientific comparison targets, 25 exploratory tables and numeric tables extracted from the final clean manuscript |
| results/reproduced/ | Fresh raw-based scoring, contrasts, quality/conformity, NLP, coding agreement, exploratory tables and figures |
| provenance/ | Source-to-publication hashes, executed-request seals, confidentiality review, environment and release verification |

The code verifies 8,000 distinct response keys, **7,995 identifiable selections**, five genuinely unknown Claude selections, 500 catalogue utilities, 2,000 policy blocks, and 4,000 cross-implementation matched stimuli. Unknown selections remain missing. Primary C−S, C−I, I−S and N−S contrasts are reconstructed using the original scenario-level bootstrap-t/t49 envelope, seed 2026102102 and 49,999 draws; Holm adjustment retains each four-test family. Three incomplete Claude full-assignment contrasts remain non-point-identified; descriptive available-pair results are kept separate. The direct Claude-minus-GPT comparisons use their own four-test family.

The 144 revised-population economic contrasts are recalculated and checked against archived estimates, confidence envelopes and Holm values. All 24 numeric rows of the final manuscript's selection, primary-contrast and quality tables are checked, including printed rounding and missing-inference labels. The exploratory reproduction verifies 25 tables covering moderator omnibus tests (15), subgroup tests (60), rationale flags (18), conformity tests (12), transitions, scenario influence and adjusted associations. Six standalone figure files are regenerated.

NLP is rerun deterministically with the unchanged frozen rules on archived text: **96,000 field/union-by-indicator codes** must match existing classifications. The original 50-response control contains 33 revised-experiment responses and 17 earlier GPT responses; historical controls never enter the 8,000-response experimental estimates. Two retained series identified by the authors as human agree on **392/400 (98.0%; unweighted Cohen's κ = 0.9647840824, rounded 0.965)**. The pre-existing final harmonized record agrees with NLP on **388/400 (97.0%)**, with 12 differences on eight responses. All final labels equal at least one initial label; the eight initial differences match A four times and B four times. No new human coding, AI annotation or harmonization is undertaken.

## Provenance, privacy and limitations

Original XLSX files are retained locally and hashed; deidentified CSV exports publish their existing labels without creator, last-editor or free-text coder-comment metadata. Source workbooks, internal ledgers, payment/authorization records, credentials, correspondence, full manuscript/response-letter documents and personal local paths are excluded. These exclusions do not remove the labels, stimuli, referent mappings or scientific outcomes needed for analytical reproduction. The raw GPT `billing` field is only the nonidentifying enum `payer=developer`, not account or payment information. See `disclosure_validation/PROVENANCE.md` and `provenance/CONFIDENTIALITY_REVIEW.md`.

The authors identify the two initial codings as human and report that AI-assisted harmonization had already occurred. Instructions prescribe separate coding and no access to NLP outputs, but execution of independence/blinding and the item-level harmonization reasoning cannot be authenticated from the retained files. Older contradictory provenance notes are preserved locally and described explicitly rather than silently rewritten. Matching labels establish value-level traceability, not the reasons or chronology of adjudication.

The control is targeted, nonrepresentative and drawn from a parent frame with documented development overlap. Neither 98% nor 97% establishes population classifier accuracy. L/A may include payment denials; B requires affirmative remuneration tied to the recognized selected option; C identifies the platform as recipient. Yes/no/uncertain/not observable remain separate categories. The indicators are not a validated transparency scale. Generated fields were requested by the schema; they do not establish spontaneous disclosure, consumer display, reading or comprehension. Rationale flags are deterministic exploratory candidates, not observations of internal reasoning or validated mediators.

Utilities/regret refer to a private synthetic benchmark, not actual consumer welfare. Some visible attributes conflict with that benchmark and equal within-option scores limit trade-off interpretations. Position, scenario domain and gap have restricted/confounded support. Policies bundle wording, salience and permission; tasks bundle preparation and confirmation. Only two configured implementations are compared. The protocol was locally dated, not publicly preregistered; later economic/NLP/mechanism analyses remain retrospective. Pointwise confidence intervals are not simultaneous Holm intervals. Reproduction verifies archived analysis, not these unmeasured constructs or provider backend determinism.

The final manuscript still has pre-existing template/Appendix A placeholders; this repository supplies the exact executed requests independently of that incomplete table. The full manuscript is not republished here. See the root `GITHUB_REPLICATION_FINAL_AUDIT.md` for the verified release scope, source exclusions and branch/PR links.

## Whole-repository anonymity review

The complete published repository, including legacy Office/PDF/image files and reachable history, has been checked for author/coder/operator identifiers. See the root ANONYMIZATION_AUDIT.md for results and platform limits. For anonymous review, a separately verified standalone ZIP is provided without Git history, hosting-account metadata or source workbook identities. The data and labels are unchanged. Private identity-term dictionaries are not published.
