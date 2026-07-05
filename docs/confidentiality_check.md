# Confidentiality Check

This report lists possible confidential, sensitive, temporary, or non-archival materials detected in the organized replication package. It reports pattern categories only and does not reproduce suspected secret values. No files were deleted.

Total suspicious findings: 72

## Summary Notes

- No private-key blocks or literal OpenAI/API-key-shaped secrets were reproduced in this report.
- The high-risk API-key findings appear to be environment-variable references or placeholders, but they should still be reviewed before public archiving.
- Binary Office files, ZIP archives, failed batch artifacts, invalid mock-run artifacts, and local path references remain the main manual-review categories.

| Suspicious file path | Suspicious pattern found | Risk level | Recommended action |
|---|---|---|---|
| `analysis/scripts/run_pilot.py` | API key assignment pattern | high | Inspect and redact if this is a real key. |
| `to_review/.env.example` | Environment file or template | high | Do not archive unless it is a sanitized example file reviewed line by line. |
| `to_review/models.yaml` | API key assignment pattern | high | Inspect and redact if this is a real key. |
| `analysis/scripts/create_full_scientific_report.py` | Private local filesystem path | medium | Replace with relative paths before public archiving if not necessary. |
| `analysis/scripts/settings.py` | Private local filesystem path | medium | Replace with relative paths before public archiving if not necessary. |
| `docs/article.md` | Email address | medium | Review whether the address is personal, institutional, or necessary citation metadata. |
| `docs/pilot_full_scientific_report_en.md` | Private local filesystem path | medium | Replace with relative paths before public archiving if not necessary. |
| `docs/pilot_methods.md` | Private local filesystem path | medium | Replace with relative paths before public archiving if not necessary. |
| `hashes/MANIFEST.json` | Private local filesystem path | medium | Replace with relative paths before public archiving if not necessary. |
| `hashes/manifest.json` | Private local filesystem path | medium | Replace with relative paths before public archiving if not necessary. |
| `to_review/DO_NOT_USE.md` | Invalid or explicitly excluded run artifact | medium | Keep in to_review or exclude from public archive unless there is a documented reason to include it. |
| `to_review/FAILURE_SUMMARY__atch_archive_failed_token_limit_batch_6a42d4d8a18c8190910af8525e07462d__42b70d97.md` | Failed/archive/batch status artifact | medium | Review for provider metadata, run identifiers, and relevance before archiving. |
| `to_review/LAST_BATCH_ID.txt` | Failed/archive/batch status artifact | medium | Review for provider metadata, run identifiers, and relevance before archiving. |
| `to_review/LAST_BATCH_ID__confirmatory_2x2_batch__a32576be.txt` | Failed/archive/batch status artifact | medium | Review for provider metadata, run identifiers, and relevance before archiving. |
| `to_review/batch_status.json` | Failed/archive/batch status artifact | medium | Review for provider metadata, run identifiers, and relevance before archiving. |
| `to_review/batch_status__confirmatory_2x2_batch__506fce58.json` | Failed/archive/batch status artifact | medium | Review for provider metadata, run identifiers, and relevance before archiving. |
| `to_review/chunk_01_BATCH_ID.txt` | Failed/archive/batch status artifact | medium | Review for provider metadata, run identifiers, and relevance before archiving. |
| `to_review/chunk_02_BATCH_ID.txt` | Failed/archive/batch status artifact | medium | Review for provider metadata, run identifiers, and relevance before archiving. |
| `to_review/chunk_03_BATCH_ID.txt` | Failed/archive/batch status artifact | medium | Review for provider metadata, run identifiers, and relevance before archiving. |
| `to_review/chunk_04_BATCH_ID.txt` | Failed/archive/batch status artifact | medium | Review for provider metadata, run identifiers, and relevance before archiving. |
| `to_review/confirmatory_2x2_corrected_v2_BATCH_ID.txt` | Failed/archive/batch status artifact | medium | Review for provider metadata, run identifiers, and relevance before archiving. |
| `to_review/confirmatory_batch_errors__ella_AI_AGENTIC_confirmatory_2x2_results_invalid_mock_run_data_raw_api__188b6ead.jsonl` | Invalid or explicitly excluded run artifact | medium | Keep in to_review or exclude from public archive unless there is a documented reason to include it. |
| `to_review/manifest.json` | Private local filesystem path | medium | Replace with relative paths before public archiving if not necessary. |
| `to_review/pilot.yaml` | Private local filesystem path | medium | Replace with relative paths before public archiving if not necessary. |
| `to_review/submission_state.json` | Failed/archive/batch status artifact | medium | Review for provider metadata, run identifiers, and relevance before archiving. |
| `to_review/submission_state__confirmatory_2x2_batch__10b1349a.json` | Failed/archive/batch status artifact | medium | Review for provider metadata, run identifiers, and relevance before archiving. |
| `analysis/scripts/create_full_scientific_report.py` | Human-subjects terminology | low | Review context to confirm no human-subject data are included. |
| `analysis/scripts/final_methodology_results.py` | Human-subjects terminology | low | Review context to confirm no human-subject data are included. |
| `data/processed/confirmatory_results_final.xlsx` | .XLSX binary/archive file | low | Review for embedded metadata, tracked changes, hidden sheets, or bundled confidential files before archiving. |
| `data/processed/pilot_results.xlsx` | .XLSX binary/archive file | low | Review for embedded metadata, tracked changes, hidden sheets, or bundled confidential files before archiving. |
| `data/raw_model_responses/chunk_03_output.jsonl` | Personal-data terminology | low | Review context to confirm the file contains documentation only, not personal data. |
| `data/raw_model_responses/chunk_04_output.jsonl` | Personal-data terminology | low | Review context to confirm the file contains documentation only, not personal data. |
| `data/raw_model_responses/confirmatory_corrected_v2_merged_output.jsonl` | Personal-data terminology | low | Review context to confirm the file contains documentation only, not personal data. |
| `data/scenarios/confirmatory_run_plan.xlsx` | .XLSX binary/archive file | low | Review for embedded metadata, tracked changes, hidden sheets, or bundled confidential files before archiving. |
| `data/scenarios/confirmatory_scenarios.xlsx` | .XLSX binary/archive file | low | Review for embedded metadata, tracked changes, hidden sheets, or bundled confidential files before archiving. |
| `data/scenarios/development_scenario_index.xlsx` | .XLSX binary/archive file | low | Review for embedded metadata, tracked changes, hidden sheets, or bundled confidential files before archiving. |
| `docs/AVAILABILITY.md` | Human-subjects terminology | low | Review context to confirm no human-subject data are included. |
| `docs/Methodologie_et_resultats_experience_confirmatoire_2x2.md` | Human-subjects terminology | low | Review context to confirm no human-subject data are included. |
| `docs/README.md` | Human-subjects terminology | low | Review context to confirm no human-subject data are included. |
| `docs/README.md` | Personal-data terminology | low | Review context to confirm the file contains documentation only, not personal data. |
| `docs/article.md` | Human-subjects terminology | low | Review context to confirm no human-subject data are included. |
| `docs/data_dictionary.md` | Human-subjects terminology | low | Review context to confirm no human-subject data are included. |
| `docs/data_dictionary.md` | Personal-data terminology | low | Review context to confirm the file contains documentation only, not personal data. |
| `docs/pilot_full_scientific_report_en.md` | Human-subjects terminology | low | Review context to confirm no human-subject data are included. |
| `docs/pilot_full_scientific_report_fr.md` | Human-subjects terminology | low | Review context to confirm no human-subject data are included. |
| `outputs/tables/descriptive_by_commission_rate.xlsx` | .XLSX binary/archive file | low | Review for embedded metadata, tracked changes, hidden sheets, or bundled confidential files before archiving. |
| `outputs/tables/descriptive_by_domain.xlsx` | .XLSX binary/archive file | low | Review for embedded metadata, tracked changes, hidden sheets, or bundled confidential files before archiving. |
| `outputs/tables/descriptive_by_scenario.xlsx` | .XLSX binary/archive file | low | Review for embedded metadata, tracked changes, hidden sheets, or bundled confidential files before archiving. |
| `outputs/tables/descriptive_by_utility_gap.xlsx` | .XLSX binary/archive file | low | Review for embedded metadata, tracked changes, hidden sheets, or bundled confidential files before archiving. |
| `outputs/tables/full_descriptive_results.xlsx` | .XLSX binary/archive file | low | Review for embedded metadata, tracked changes, hidden sheets, or bundled confidential files before archiving. |
| `outputs/tables/hypotheses_table.xlsx` | .XLSX binary/archive file | low | Review for embedded metadata, tracked changes, hidden sheets, or bundled confidential files before archiving. |
| `outputs/tables/hypothesis_summary.xlsx` | .XLSX binary/archive file | low | Review for embedded metadata, tracked changes, hidden sheets, or bundled confidential files before archiving. |
| `outputs/tables/scenario_level_results.xlsx` | .XLSX binary/archive file | low | Review for embedded metadata, tracked changes, hidden sheets, or bundled confidential files before archiving. |
| `outputs/tables/table1_design.xlsx` | .XLSX binary/archive file | low | Review for embedded metadata, tracked changes, hidden sheets, or bundled confidential files before archiving. |
| `outputs/tables/table2_domain_condition_counts.xlsx` | .XLSX binary/archive file | low | Review for embedded metadata, tracked changes, hidden sheets, or bundled confidential files before archiving. |
| `outputs/tables/table3_descriptive_by_condition.xlsx` | .XLSX binary/archive file | low | Review for embedded metadata, tracked changes, hidden sheets, or bundled confidential files before archiving. |
| `outputs/tables/table4_partner_model.xlsx` | .XLSX binary/archive file | low | Review for embedded metadata, tracked changes, hidden sheets, or bundled confidential files before archiving. |
| `outputs/tables/table5_marginal_effects_contrasts.xlsx` | .XLSX binary/archive file | low | Review for embedded metadata, tracked changes, hidden sheets, or bundled confidential files before archiving. |
| `outputs/tables/table6_optimal_and_regret_models.xlsx` | .XLSX binary/archive file | low | Review for embedded metadata, tracked changes, hidden sheets, or bundled confidential files before archiving. |
| `outputs/tables/table7_disclosure.xlsx` | .XLSX binary/archive file | low | Review for embedded metadata, tracked changes, hidden sheets, or bundled confidential files before archiving. |
| `outputs/tables/table8_hypothesis_synthesis.xlsx` | .XLSX binary/archive file | low | Review for embedded metadata, tracked changes, hidden sheets, or bundled confidential files before archiving. |
| `outputs/tables/table9_robustness.xlsx` | .XLSX binary/archive file | low | Review for embedded metadata, tracked changes, hidden sheets, or bundled confidential files before archiving. |
| `to_review/AI_AGENTIC_PILOT_REPORT_PACKAGE.zip` | .ZIP binary/archive file | low | Review for embedded metadata, tracked changes, hidden sheets, or bundled confidential files before archiving. |
| `to_review/Methodologie_et_resultats_experience_confirmatoire_2x2.docx` | .DOCX binary/archive file | low | Review for embedded metadata, tracked changes, hidden sheets, or bundled confidential files before archiving. |
| `to_review/Who_Decides_When_the_Agent_Chooses_FINAL.docx` | .DOCX binary/archive file | low | Review for embedded metadata, tracked changes, hidden sheets, or bundled confidential files before archiving. |
| `to_review/Who_Decides_When_the_Agent_Chooses_REVISED_manuscript.docx` | .DOCX binary/archive file | low | Review for embedded metadata, tracked changes, hidden sheets, or bundled confidential files before archiving. |
| `to_review/_original_manuscript.docx` | .DOCX binary/archive file | low | Review for embedded metadata, tracked changes, hidden sheets, or bundled confidential files before archiving. |
| `to_review/confirmatory_2x2_design_report_fr.docx` | .DOCX binary/archive file | low | Review for embedded metadata, tracked changes, hidden sheets, or bundled confidential files before archiving. |
| `to_review/confirmatory_results.xlsx` | .XLSX binary/archive file | low | Review for embedded metadata, tracked changes, hidden sheets, or bundled confidential files before archiving. |
| `to_review/confirmatory_v2_design_report_fr.docx` | .DOCX binary/archive file | low | Review for embedded metadata, tracked changes, hidden sheets, or bundled confidential files before archiving. |
| `to_review/mock_results.xlsx` | .XLSX binary/archive file | low | Review for embedded metadata, tracked changes, hidden sheets, or bundled confidential files before archiving. |
| `to_review/pilot_full_scientific_report_fr.docx` | .DOCX binary/archive file | low | Review for embedded metadata, tracked changes, hidden sheets, or bundled confidential files before archiving. |
