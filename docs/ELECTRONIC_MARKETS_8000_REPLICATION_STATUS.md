# Electronic Markets revised study — replication status (3 November 2026)

**Status: INCOMPLETE for the revised 8,000-response study.** This is a scope and deposit checklist, **not** a release of the new experimental inputs. No experimental instruction is reconstructed or represented here as verbatim unless supported by the deposited request files.

## Two different experimental designs

The material already present in this repository primarily documents an **earlier confirmatory 2 × 2 design** (neutral/commercial instructions × recommendation/action preparation), with source names such as `confirmatory_2000_requests_corrected_v2.jsonl`. In particular, [S1 experimental materials](S1_experimental_materials.md) quotes instructions for that earlier design. **Those are not the four N/S/I/C policies of the subsequently revised _Electronic Markets_ manuscript** and must not be cited as their verbatim text.

The revised manuscript, **“Who decides when the agent chooses? Platform commercial instructions in delegated selection”** (submission ELMA-D-26-01628), reports a separate experiment: 50 synthetic scenarios (20 hotels, 15 software, 15 electronics) × 2 implementations (GPT and Claude) × 4 policy conditions × 2 tasks × 10 repetitions = **8,000 generated responses**.

The policies are:
- **N:** explicit neutrality;
- **S:** no commercial-priority instruction (silence);
- **I:** information about a commercial commission;
- **C:** the commission information plus *conditional permission* to favor an eligible partner. The manuscript quotes the non-obligation clause “You are never required to select this option.”

These descriptions are **not** substitutes for the full input bytes sent to each model. API-specific formatting can differ even where substantive instructions are matched.

## Files required before the revised manuscript can point here instead of reproducing its Appendix A

| Required evidence | Status |
| --- | --- |
| Exact **common instruction** and **N/S/I/C policy instructions** as sent, including any scenario-specific substitutions and full clause C | **Not deposited / not verified here** |
| Prompt/request provenance: per-implementation request constructors or exact archived requests; user-message template; tool definition and output schema | **Not deposited for the revised 8,000-response study** |
| Scenario catalogue and assignment/partner mapping for the revised 50 scenarios | **Not deposited for this study** |
| Raw model responses and reproducible analysis-ready outputs for both implementations | **Not deposited for this study** |
| Reproduction scripts for primary contrasts (including scenario-level aggregation, uncertainty, and corrections) and text-classification rule version | **Not deposited for this study** |
| Frozen version identifiers, hash manifest, environment details, and a verified no-credential/no-private-data scan | **Not deposited for this study** |
| Documentation of targeted text-control analysis, including denominators, label definitions, and provenance limitations | **Summary below; underlying local artifacts not deposited** |

**Do not infer that the existing 2 × 2 prompts, files, tables, or code fulfill any of these revised-study requirements.** Existing historical files should remain preserved and clearly labeled, not silently relabeled or overwritten.

## Text-control coding: author-reported and locally verified summary

According to the author’s 3 November 2026 local verification dossier, a targeted control covered 50 archived responses, including **33** from the revised main experiment and **17** historical responses. Each response had two text fields and four nominal coding indicators (**400** paired assessments). Two coding series were reported as human; their recorded labels agreed on **392/400 (98.0%; unweighted Cohen’s κ = 0.965)**, with eight differences. The author reports that the final record had already been harmonized with AI assistance; the final record agreed with frozen NLP v2.2.0 labels on **388/400 (97.0%)**, with 12 differences.

**Scope and provenance:** The classification agreements are distinct. The 97.0% is *not* an inter-rater statistic, an independent population-level accuracy estimate, or proof that consumers saw or understood any generated disclosure. The control sample is targeted, not representative. The independence/blinding of coding and exact history of AI-assisted harmonization are not independently authenticated by the retained local coding files. This public repository has **not** yet been furnished with those files, so the summary here is not independently reproducible from this GitHub checkout.

Do not upload identifiable coder metadata, private annotations, API credentials, or raw internal project files without an explicit disclosure review. A suitable release may use an approved anonymized trace or aggregate table, with retained hashes and a statement of restrictions.

## Release/verification gates

1. Extract the exact **five instruction blocks** (common + N/S/I/C) from the frozen executed requests or source constructor, preserving the actual transmitted strings; record when blocks vary by scenario or implementation. Do not retype from the manuscript or create plausible replacements.
2. Validate that the common content, policy-specific differences, tool payload, and scenario substitutions match the archived requests for **both** implementations.
3. Publish a versioned source/manifest mapping each deposited file to the revised experiment, with cryptographic hashes and run parameters. Keep legacy 2 × 2 files under their existing identities.
4. Inspect everything for credentials, user-identifiable or private records, and non-public human coding material before pushing to this **public** repository.
5. Verify a clean checkout reproduces the principal reported summaries and keep an explicit record of unsupported components.
6. Only after all required instructions are actually present and accessible should the revised manuscript replace Appendix A with an unconditional GitHub availability statement. Until then, retain the verbatim instructions in the submission or supply them as a complete supplementary file.

This note changes no experimental data, prompt, model output, or result and does not certify completion of the revised-study replication deposit.
