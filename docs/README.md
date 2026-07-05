# Who Decides When the Agent Chooses?

Replication package for the academic article **"Who Decides When the Agent Chooses? Commercial Incentives and the Agentic Opacity of Delegated Choice"**.

This repository contains the materials needed to inspect and reproduce the study workflow: synthetic decision scenarios, prompts, raw model outputs, processed analysis datasets, scripts, robustness materials, tables, figures, hashes, and documentation. It is intended as a clean public-facing replication package.

No empirical results are introduced in this README. Tables, figures, estimates, and sample counts should be taken from the manuscript and the archived analysis outputs.

## Data Statement

The data in this repository consist of synthetic decision scenarios and model-generated outputs. The repository contains no personal data and no human-subject data.

Before publication, the repository will be archived on Zenodo or OSF so that the published article points to a fixed, persistent version of the replication materials.

## Repository Structure

```text
.
├── README.md
├── LICENSE
├── CITATION.cff
├── requirements.txt
├── data/
│   ├── scenarios/
│   ├── raw_model_responses/
│   └── processed/
├── prompts/
│   ├── system_prompts/
│   └── user_prompts/
├── analysis/
│   ├── scripts/
│   └── robustness/
├── outputs/
│   ├── tables/
│   └── figures/
├── hashes/
├── docs/
└── to_review/
```

## Folder Contents

- `data/scenarios/`: locked scenario files, scenario catalogues, run plans, option sets, utility metadata, partner-option metadata, and model-visible scenario files.
- `data/raw_model_responses/`: raw JSONL request and response files, Batch API outputs, chunked response exports, and other unprocessed model-output files.
- `data/processed/`: cleaned, merged, scored, and analysis-ready datasets. The primary confirmatory analysis dataset is `confirmatory_results_final.csv`.
- `prompts/system_prompts/`: condition-level and system-style prompts used to instruct the model.
- `prompts/user_prompts/`: user-message prompts, scenario prompt manifests, and prompt-construction metadata.
- `analysis/scripts/`: copied analysis, parsing, scoring, validation, table-generation, figure-generation, and reproduction scripts.
- `analysis/robustness/`: robustness-check scripts and outputs, including validity checks and sensitivity-analysis materials.
- `outputs/tables/`: final and supplementary tabular outputs.
- `outputs/figures/`: final and supplementary figure outputs.
- `hashes/`: SHA-256 manifests, locked-artifact hashes, provenance files, and integrity-check materials.
- `docs/`: repository documentation, data dictionary, software-version notes, reproduction instructions, file inventory, and confidentiality check.
- `to_review/`: files requiring manual review before public archiving, such as failed-run artifacts, Word documents, archive files, schemas, configs, or metadata files.

## Reproduction Overview

The main reproduction workflow is:

1. Create a clean Python environment and install the required packages.
2. Inspect locked scenarios and run-plan files in `data/scenarios/`.
3. Inspect prompts in `prompts/system_prompts/` and `prompts/user_prompts/`.
4. Parse raw model responses from `data/raw_model_responses/`.
5. Score parsed responses against the locked scenario metadata.
6. Generate or verify the processed dataset in `data/processed/`.
7. Re-run the main statistical analyses and robustness checks.
8. Regenerate or verify tables in `outputs/tables/` and figures in `outputs/figures/`.
9. Verify file integrity using the hash files in `hashes/`.

Detailed commands and caveats are provided in `docs/reproduction_instructions.md`. Variable definitions are provided in `docs/data_dictionary.md`, and software details are provided in `docs/software_versions.md`.

## Basic Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Some copied scripts preserve imports and paths from the original development tree. When re-running scripts, use the original source layout where applicable or consult `docs/file_inventory.md` to map copied package files back to their original locations.

## Citation

Please cite both the published article and the archived replication package. Citation metadata should be updated in `CITATION.cff` once final publication and archive details are available.
