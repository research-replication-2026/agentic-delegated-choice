# Electronic Markets revised replication: final audit

**Date:** 3 November 2026. **Verdict: COMPLET — offline analytical replication of the archived revised study.** This verdict concerns availability and checked reproducibility of archived analyses, not new model generation, population measurement validity or consumer exposure.

Article: *Who decides when the agent chooses? Platform commercial instructions in delegated selection* (ELMA-D-26-01628).

- [Dedicated branch](https://github.com/research-replication-2026/agentic-delegated-choice/tree/electronic-markets-replication-readiness-20261103)
- [Pull request #1](https://github.com/research-replication-2026/agentic-delegated-choice/pull/1)
- [Replication instructions](revised_8000/README.md)

The pre-existing branch was inspected at commit `4263123d73103710a5e8d02e8e28562cb1aab4d8`; PR #1 was open and draft, with base `main`. This update uses that branch. It does not merge or write directly to `main`.

## Release count and preservation

The initial analytical-release change published or updated **146 files: 144 additions and two documentation replacements**, including **140 files under revised_8000/**. Later anonymity-audit additions are documented separately in ANONYMIZATION_AUDIT.md. The earlier repository's scientific files remain unchanged; only the root README and the revised-study status note are replaced to identify the current package. The preceding README is archived byte-for-byte. Additional files outside revised_8000 are that archive, the root README, the status note, this audit, byte-preserving Git attributes and an offline analytical CI workflow. Exact counts and Git blob hashes are recorded in the publication manifest accompanying the local audit; repository file counts refer to files, not 8,000 individual response artifacts.

The local research originals, including Excel source workbooks, requests, responses, classifying rules, manuscript and scoring sources, were protected by SHA-256 before assembly and checked afterwards. No original was modified. Publication projections, portable adapters and new reports were written to an isolated repository checkout, not over research source files. `provenance/source_to_release_manifest.csv` maps public inputs to original relative source aliases, source hashes and explicit transformations; the local full inventory retains absolute paths without publishing them.

## Available materials

| Required component | Released evidence |
|---|---|
| 50 scenarios and catalogues | Synthetic options, constraints, private benchmark scores and targets in data/scenarios.json |
| Actual common/policy/task instructions | All 8,000 archived request payloads, including all scenario-specific IDs/rates and provider-specific tool/configuration fields; eight exact examples, not rewritten instructions |
| Execution provenance | GPT request hashes match the dated freeze; four Claude canonical submitted-payload hashes match the read-only operational ledger, all in retrieved state; only nonidentifying seal summaries released |
| Assignments | Complete 4,000 GPT keys and 4,000 Claude-to-source correspondence records; synthetic identifiers, no participants |
| Raw outputs | 4,000 GPT and 4,000 Claude original provider response envelopes, losslessly compressed |
| Processing/scoring/inference | Unchanged original scorers/inference plus portable offline adapters; no provider SDK or execution client required |
| NLP | Unchanged v2.2.0 rule/adapter files and original freeze hashes, codebook, archived classifications and raw-text rerun |
| Existing human control | Three deidentified original-label projections (A, B, final), original workbook hashes, 50 text/referent contexts and full comparison outputs |
| Manuscript results | Archived scientific references, the three final numeric tables, fresh scores/contrasts/quality/NLP/coding results and 25 checked exploratory tables |
| Provenance and versions | Input hashes, scientific environment, source mapping, exclusions, release and confidentiality checks |

Lossless gzip avoids changing request/response bytes and keeps the complete deposit modest in size. Original instructions are never reconstructed from the manuscript's Appendix A. Archival generation source is included for provenance; portable reproduction reads the already executed materials and does not regenerate scenarios or stimuli.

## Executed checks and results

| Check | Result |
|---|---|
| Main responses/assignments | **8,000** distinct response keys, 4,000 per implementation |
| Recognized selections | **7,995**; five Claude choices remain unknown (two N, three S) |
| Researcher utility reconstruction | All **500** option utility values recomputed from archived scores/weights/constraints |
| Exact input pairing | **2,000** complete policy blocks and **4,000** cross-implementation matched system/user/schema payloads |
| Main estimates | Per-model/policy partner rates match raw data and final manuscript |
| Primary contrasts | C−S, C−I, I−S, N−S; original seed 2026102102 and 49,999 draws; original bootstrap-t/t49 confidence envelopes, Bonferroni envelopes, Holm families and missing-outcome bounds reproduced |
| Interimplementation comparisons | Direct Claude-minus-GPT scenario comparisons and separate four-test Holm adjustments reproduce archived values; incomplete full-assignment tests remain unavailable |
| Quality/conformity | Optimal choice, absolute/normalized regret, hard-constraint violations, completion, schema conformity and frozen fully-conformant outcomes reproduce references |
| Economic analyses | **144** revised-population comparisons reproduce archived estimates and, when estimable, confidence intervals and Holm values |
| Final manuscript tables | **24/24 numeric rows** checked in selection, primary-contrast and benchmark-quality tables, including print rounding and withheld-inference labels |
| NLP rerun | **96,000** exact field/union indicator classifications match archived labels; 96 complete model/policy/field/indicator summaries verified |
| Initial A–B agreement | **392/400 = 98.0%; unweighted Cohen's κ = 0.9647840824052472**, rounded .965; eight differences on eight responses |
| Harmonized label trace | All 392 shared labels retained; four initially differing final labels match A and four match B; no final label outside the initial pair |
| Final versus NLP | **388/400 = 97.0%**, 12 differences across eight responses |
| Exploratory analysis | Unchanged archived script reproduces **25 tables**, moderator/subgroup/rationale/conformity families of 15/60/18/12 tests and six figure files |
| Clean-checkout replication | Repeated from a clean Git-tree export, with reads of private research sources blocked; only the isolated checkout and installed scientific runtime were allowed |
| Network/model calls | Analysis sockets blocked; **zero model/API calls**, no experiments, annotation or harmonization rerun |
| Publication scan | New release and decompressed archives reviewed for credential signatures, private keys, personal paths and addresses; no unresolved findings |

The pooled initial κ uses four nominal categories. Missing text remains not observable; uncertainty/nonobservability are categories, not zero-filled negatives. Initial and final-record–NLP agreement measure different comparisons. Their differing disagreement keys are not relabeled or adjudicated again.

All numerical checks passed. **No discrepancy with the final manuscript's checked numeric tables or archived scientific reference coefficients was found.** Rounded p-values and confidence limits are compared at their printed precision; unrounded analytical values remain available. The three incomplete Claude full-assignment contrasts are not assigned invented point estimates or p-values.

## Privacy decisions and source limitations

Original workbooks with creator/editor metadata and free-text comments are not uploaded. Their scientific labels are published as deidentified CSV with original source hashes. Internal account/payment/authorization records, SQLite ledgers, credentials, full manuscripts, reviewer correspondence and local absolute paths are excluded. A personal path in a historical manuscript-integrity guard is replaced in the public archival copy only; no experimental text changes. Original raw experiment files remain byte-identical after decompression. See [the confidentiality review](revised_8000/provenance/CONFIDENTIALITY_REVIEW.md).

The two existing human coding series have been verified against the archived response identifiers, texts and coding units. All 400 matched assessments were checked and their agreement was recalculated as 392/400 (98.0%; Cohen's κ = 0.965). The existing AI-assisted harmonized annotations were traced to those initial labels, and their separate 388/400 concordance with NLP was reproduced. The coding provenance identifies the exact source files and SHA-256 hashes; no coding or harmonization was redone.

The control is targeted (33 current, 17 historical), nonrepresentative, and its parent frame has known development overlap. It does not establish population classifier accuracy. Generated text was requested by the response schema; neither coding nor NLP establishes consumer display, reading or comprehension. Utilities represent an imperfect private synthetic benchmark, not consumer welfare. Exploratory position/gap/domain/rationale findings retain their retrospective, confounded and nonmechanistic interpretation.

The final local manuscript contains pre-existing editorial placeholders in its template and Appendix A instruction table. These were not filled with invented text. Exact executed requests are available in this release independently of those placeholders. The full manuscript is not deposited publicly; its source hash and exact numeric table projections identify the version used for confrontation. The verification concerns the retained coding files, their matched labels and the reported analytical results. Provider backend determinism and unmeasured consumer outcomes are outside that analytical scope.

## Reproduction and branch handling

Run the three commands in [revised_8000/README.md](revised_8000/README.md). `RELEASE_SHA256.json` pins immutable code/materials/reference outputs. Regenerated scientific outputs are checked against those references rather than compared as timestamp-sensitive ZIP/PDF bytes. The analytical CI workflow performs dependency installation followed by the same offline commands; it does not call models or run historical submission scripts.

The dedicated branch and PR are updated without force-pushing or merging. The old 2 × 2 experiment remains available under its own identity. A clean local analytical run is recorded separately from any subsequent GitHub Actions status; an unobserved hosted-CI result is not presented as a completed hosted run.

## Hosted clean-checkout verification

After publication of analytical commit `0fc357452a85e30db728cab6b88ffca29849b9cc`, [GitHub Actions run 41698430852](https://github.com/research-replication-2026/agentic-delegated-choice/actions/runs/41698430852) completed successfully. Checkout, Python setup, installation of the pinned dependencies, raw scoring/inference/NLP/control reproduction, exploratory reproduction, and release integrity/confidentiality checks all passed. This independently verifies the portable commands on a GitHub-hosted Ubuntu runner with Python 3.11, in addition to the guarded local clean-export run on Python 3.9. No provider credentials or model calls were used. The subsequent audit-only commit records this observed result without altering any analytical code, input or scientific output.
