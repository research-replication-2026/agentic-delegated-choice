# Who Decides When the Agent Chooses?

Replication package for the academic article **"Who Decides When the Agent Chooses? Commercial Incentives and the Agentic Opacity of Delegated Choice"**.

This repository is prepared to support transparent reproduction of the experiment, data processing workflow, statistical analyses, robustness checks, tables, figures, and archival materials associated with the article. It is intended as a clean public-facing package rather than a working notebook of exploratory development.

No empirical results are reported in this README. Reported estimates, sample sizes, tables, and figures should be taken from the manuscript and reproduced by the scripts in this repository.

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
└── docs/
    ├── data_dictionary.md
    ├── software_versions.md
    └── reproduction_instructions.md
```

## Purpose

The repository documents and reproduces an experiment on delegated choice by language-model agents under varying commercial incentives. The study uses synthetic decision scenarios and model-generated responses to examine how agentic systems present, select, and disclose options when commercial incentives may conflict with user-facing choice quality.

The replication package is designed to make the following materials inspectable and reproducible:

- synthetic decision scenarios used in the experiment;
- system and user prompts used to generate model responses;
- raw model-generated outputs;
- processed analysis datasets derived from those outputs;
- scripts used for cleaning, scoring, analysis, and robustness checks;
- tables, figures, and supporting hashes or integrity checks.

## Data and Materials

The dataset contains only synthetic decision scenarios and model-generated outputs. It contains no personal data and no human-subject data.

The main material types are separated as follows:

- `data/scenarios/` contains the synthetic decision scenarios supplied to the model.
- `data/raw_model_responses/` contains raw model outputs as returned by the model provider or collection pipeline.
- `data/processed/` contains cleaned, parsed, scored, or otherwise analysis-ready datasets derived from the raw responses.
- `prompts/system_prompts/` contains system-level instructions used during model calls.
- `prompts/user_prompts/` contains user-facing prompts or prompt templates used for each scenario or condition.
- `analysis/scripts/` contains scripts for data preparation, scoring, statistical analysis, and table or figure generation.
- `analysis/robustness/` contains scripts and outputs for robustness checks and sensitivity analyses.
- `outputs/tables/` contains reproducible tables generated from the analysis scripts.
- `outputs/figures/` contains reproducible figures generated from the analysis scripts.
- `hashes/` contains checksums or other integrity files used to document fixed inputs, raw outputs, processed datasets, or generated artifacts.

## Reproduction Workflow

The intended reproduction workflow is:

1. Create a clean Python environment.
2. Install the software dependencies listed in `requirements.txt`.
3. Inspect the data dictionary in `docs/data_dictionary.md`.
4. Verify software versions against `docs/software_versions.md`.
5. Follow the full step-by-step procedure in `docs/reproduction_instructions.md`.
6. Run the data-processing scripts in `analysis/scripts/`.
7. Run the statistical analysis and robustness scripts.
8. Regenerate tables in `outputs/tables/` and figures in `outputs/figures/`.
9. Compare generated files against the documented hashes in `hashes/`, where applicable.

Example setup:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The exact commands for reproducing the experiment and analyses should be maintained in `docs/reproduction_instructions.md` as the replication package is finalized.

## Archival Plan

Before publication, this repository will be archived on Zenodo or OSF. The archived version will provide a persistent identifier and a fixed snapshot of the replication materials corresponding to the published article.

## Citation

Please cite the published article and the archived replication package. Citation metadata will be maintained in `CITATION.cff` once the final publication and archival details are available.
