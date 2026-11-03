# Revised study: output-based analytical distribution

**Status: PARTIEL for full protocol replication.** Executed system/user messages, free-text scenario queries, instruction examples and reconstruction source are not supplied. This is an analysis release based on archived model outputs and synthetic assignment metadata, not a release of the executed inputs.

## Reproduce

```bash
python -m pip install -r revised_8000/analysis/requirements.txt
python -B revised_8000/analysis/reproduce.py
python -B revised_8000/analysis/reproduce_mechanisms.py
python -B revised_8000/analysis/check_release.py
```

The commands make no model/API calls and block network sockets during scientific analysis. Outputs are written only to results/reproduced/. Dependencies are pinned in analysis/requirements.txt.

## Available data and verified results

The revised study comprises 50 synthetic scenarios, GPT and Claude, four policy conditions N/S/I/C, two simulated tasks and ten repetitions (8,000 records). Conditions are retained as analytical labels. Provider parameters are supplied as numerical/API configuration metadata without message text. The structural output schema omits descriptive input prose; it is used only for output-conformity scoring, not represented as an executed request.

- data/scenarios.json retains numerical catalogues, constraints, weights and benchmark values; free-text scenario queries are excluded. Original full-scenario hashes are labelled as original_scenario_hash.
- data/raw/ now contains **projections of archived output envelopes**, not full original transport envelopes. Function-call arguments / tool-use decision objects, generated text, completion status, model settings and usage required for analysis are preserved exactly. Instruction/echo fields, input schemas and redundant transport metadata are excluded.
- Assignments preserve synthetic record correspondence, policy/task labels, catalogue mappings, repetition and scenario membership. No participant identities are involved.
- data/decision_schema.json is structural only. data/protocol_settings.json contains the archived sampling/tool-choice configuration without message bodies.
- data/processed/ and results/reference/ contain scientific comparison targets, not inputs used to fabricate estimates.

The analytical commands reconstruct **8,000 responses, 7,995 identifiable selections and five unknown Claude choices**; all 500 benchmark option utilities; partner-selection rates; original four-test primary/cross-implementation families; confidence envelopes and Holm adjustments; conformity and economic outcomes; 144 economic comparisons; 96,000 frozen NLP classifications; and 24 numeric rows of the final manuscript's three result tables. All match the archived targets.

The exploratory adapter reproduces **24 numerical reference tables** and six figure files. The former input-message verification table is not reproduced as a source check; a separate commission-allocation table refers only to assignment metadata. Exact input equality and executed wording are not verifiable from this public distribution and are not claimed. Analytical code has been adapted for output-only I/O; numerical routines and frozen NLP v2.2.0 are retained.

## Verified existing coding control

The two existing human coding series have been verified item by item for the same 50 responses and 400 field-by-indicator units. Agreement is **392/400 (98.0%; unweighted Cohen's κ = 0.9647840824, rounded 0.965)**. AI-assisted harmonization had already been performed; no coding or harmonization was redone. Every final label matches at least one initial label, with four initial differences matching A and four matching B. The separate final-record–NLP comparison reproduces **388/400 (97.0%)**, with 12 differences on eight responses.

The control contains 33 current-experiment and 17 historical responses. Historical controls never enter the 8,000-response experimental estimates. Personal workbook metadata/comments are excluded from the deidentified label projections. The sample is targeted and nonrepresentative; neither agreement establishes population classifier accuracy, consumer display or comprehension. Generated text was requested by the response format and is not a measure of spontaneous disclosure. The four nominal categories remain separate.

## Scope, confidentiality and limitations

No executed input messages or reconstruction source appear in this current distribution. Generated answers may reflect experimental conditions; they are preserved as outputs because changing them would invalidate the text analysis. Policy labels, synthetic option IDs and numerical benchmark data are analytical variables, not published message bodies. Full input-to-output protocol reproduction is unavailable by this publication choice, so the global verdict is PARTIEL even though the supplied output-based analyses reproduce their targets.

Source originals remain unchanged and retained privately. Source-to-release transformations and withheld-file hashes are documented in provenance/. No instruction is invented or approximately reconstructed. Older legacy materials containing inputs are withdrawn from the current tree; remaining legacy results are not presented as this protocol.

Utilities measure a private synthetic benchmark, not real welfare. Some visible attributes conflict with that target. Exploratory associations retain their retrospective/confounded interpretation. Five unknown choices remain missing; no replacement outcomes are invented. Text classification does not prove actual consumer exposure or internal model reasoning.

Current-file withdrawal does not remove older public commits, the default branch, cached URLs or previously downloaded copies. Repository-history/visibility controls are separate. The anonymous output-analysis ZIP omits Git and hosting metadata; no absolute unlinkability guarantee is made.
