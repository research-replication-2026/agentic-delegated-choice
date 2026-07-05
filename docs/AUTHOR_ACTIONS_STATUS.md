# Author Actions Status

Tracks every author-action marker present in `manuscript/article.md` as of the
P0 repair (8 markers) through final resolution. No marker was resolved by
inventing data, results, formulas, dates, DOIs, or references; no
already-published number was altered; every inserted number traces to a script
under `analysis/repro/` or to a fetched arXiv source for M1.

| # | Original marker (§, abbreviated) | Status | Evidence | Manuscript location |
|---|---|---|---|---|
| 1 | §2.2 — add verified source(s) on controlled audits of commercial steering in LLM/agent recommendations | **RESOLVED** | arXiv pages for Kumar & Lakkaraju (2024), Filandrianos et al. (2025), and Liu (2026), cited in article references | article.md §1 |
| 2 | §5.5 — insert exact utility function and utility_regret/normalized_regret formulas | **RESOLVED** (T1) | `analysis/repro/verify_regret_formula.py` → `REGRET_FORMULA_CHECK.md` | article.md §5.5; supplement/S4_measures_and_robustness.md §S4.1 |
| 3 | §5.6 — document coding of partner_position | **RESOLVED** (T3) | `analysis/repro/verify_partner_position.py` → `PARTNER_POSITION_CHECK.md`, `FULL_COEFFICIENT_TABLES.md` | article.md §5.6; supplement/S4_measures_and_robustness.md §S4.2–S4.3 |
| 4 | §5.6 — run at least one small-cluster robustness analysis | **RESOLVED** (T4) | `analysis/repro/robustness_small_cluster.py` → `manuscript/supplement/S4_robustness/*.md` | article.md §5.6, §6.6, Table 6 Panel B |
| 5 | §5.7 — insert exact collection dates of the four batches | **RESOLVED** | `analysis/repro/extract_collection_dates.py` → `COLLECTION_DATES.md`; batch submission records and observed completion confirmation window | article.md §5.7 |
| 6 | §5.7 — confirm whether statistical models/outcome definitions were locked before outcome inspection | **RESOLVED** (T6) | `analysis/repro/verify_locked_before_collection.py` → `LOCKED_BEFORE_COLLECTION_CHECK.md` | article.md §5.7 |
| 7 | §5.7 — specify the data and code availability statement | **RESOLVED** | Author-provided statement inserted verbatim; supporting inventory in `manuscript/AVAILABILITY.md`; `analysis/repro/verify_availability_scaffold.py` → `AVAILABILITY_SCAFFOLD_CHECK.md` | article.md §5.7 |
| 8 | §6.5 — state the automatic disclosure-coding rule, examples, false positive/negative discussion, and no independent human validation | **RESOLVED** | `analysis/repro/disclosure_coding_audit.py` → `DISCLOSURE_CODING_AUDIT.md`; `manuscript/supplement/validation/disclosure_diagnostic_extract.csv` + `coding_sheet.md`; limitation retained in §9 | article.md §6.5 and §9; supplement/S4_measures_and_robustness.md §S4.4 |

## Summary

- **8 of 8** original markers are resolved in `manuscript/article.md`.
- The author block was inserted from the author-provided text.
- `manuscript/Who_Decides_When_the_Agent_Chooses_FINAL.docx` was rebuilt from the resolved manuscript.

## Verification chain

Every task in T0–T9 ran the rule-4 hash gate first (`analysis/repro/verify_published_numbers.py::hash_gate`, reused by every subsequent script) and confirmed merged data, locked scenario set, and locked run plan match the required SHA-256 values before any computation. `analysis/repro/VERIFICATION_REPORT.md` (T0) shows 70/70 manuscript-published numbers and 7/7 cross-checks against `results/tables/confirmatory_final/*.csv` PASS — zero discrepancies were found anywhere in this work, so no **DISCREPANCY** status appears in the table above.

`manuscript/Who_Decides_When_the_Agent_Chooses_FINAL.docx` was built with
Pandoc from `manuscript/article.md` and verified to contain all six embedded
figures and all six table labels on DOCX round-trip.
