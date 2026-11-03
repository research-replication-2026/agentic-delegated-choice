# Data and Code Availability Statement

The data and code that support the findings of this study are available from
the corresponding author upon reasonable request.

## What exists and is ready to be published as-is

- **Locked scenario set and run plan** (`confirmatory_2x2/data/locked/`):
  `confirmatory_scenarios.json`, `confirmatory_run_plan.csv`,
  `LOCKED_SET_HASH.txt`, `RUN_PLAN_HASH.txt` — SHA-256 hashes reported in
  the manuscript and reproduced in `analysis/repro/verify_published_numbers.py`.
- **Raw collected data**: `confirmatory_2x2/data/raw_api/confirmatory_corrected_v2_merged_output.jsonl`
  (SHA-256: `9ad195935d60025f9cff02ef290aebd829c9809b273f16a1d27bd2015dedd4b9`).
- **Processed results**: `confirmatory_2x2/data/processed/confirmatory_results_final.csv`
  and `confirmatory_2x2/results/tables/confirmatory_final/*.csv`.
- **All experimental materials**: system prompts (`confirmatory_2x2/prompts/`),
  output schema (`confirmatory_2x2/schemas/submit_agentic_decision.json`),
  reproduced verbatim in `manuscript/supplement/S1_experimental_materials.md`.
- **All analysis code**: `confirmatory_2x2/src/` (data collection, scoring,
  statistical models) and `analysis/repro/` (independent verification
  scripts, run against the raw data with no dependency on `confirmatory_2x2/src/final_methodology_results.py`).
- **Manuscript source**: `manuscript/article.md` (pandoc-convertible Markdown)
  and the supplementary materials under `manuscript/supplement/`.

## Restrictions

No human subjects data, proprietary third-party data, or API credentials are
included in the materials above (verified live against the submitted batch file
by `analysis/repro/verify_availability_scaffold.py`, using
`confirmatory_2x2/src/build_corrected_batch.py::contains_secret_or_real_action`;
report: `analysis/repro/AVAILABILITY_SCAFFOLD_CHECK.md` — no secret pattern,
no real-transaction-endpoint pattern found).
