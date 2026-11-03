# Archived output analyses — revised Electronic Markets study

This distribution provides analytical data and code for the revised 8,000-response study. **No executed model-input messages or reconstruction source are distributed in this version.** Full protocol replication is therefore **PARTIEL**; output-based statistical reproduction remains available.

```bash
python -m pip install -r revised_8000/analysis/requirements.txt
python -B revised_8000/analysis/reproduce.py
python -B revised_8000/analysis/reproduce_mechanisms.py
python -B revised_8000/analysis/check_release.py
```

The output projections preserve 8,000 archived decisions and generated text, with 7,995 identifiable selections. Input/echo fields and descriptive tool text have been excluded. Scientific values, initial coding labels, final labels and NLP rules are unchanged. Initial double-coding agreement is verified at 392/400 (98.0%; Cohen's κ = 0.965); final harmonized-record–NLP concordance is separately 388/400 (97.0%).

See [the analysis guide](revised_8000/README.md), [the current audit](GITHUB_REPLICATION_FINAL_AUDIT.md) and [the anonymity audit](ANONYMIZATION_AUDIT.md). The anonymous outputs-only ZIP can be downloaded from this branch as ANONYMOUS_OUTPUT_ANALYSIS_8000.zip.

## Scope and historical access

The remaining legacy results concern a separate earlier experiment. Files containing input material, example messages or reconstruction code are withheld from the current tree; historical source data are retained privately without modification. Do not use legacy results as the revised design.

**Deleting current files is not a historical purge.** Earlier GitHub commits, `main`, cached URLs and copies already downloaded may still expose previously published material. This update does not claim otherwise, does not rewrite history and does not merge into `main`. Fully withdrawing previous public access requires a separate repository-visibility/history action.
