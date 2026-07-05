# agentic-opacity-delegated-choice

# Who Decides When the Agent Chooses?

Replication package for the academic article: **Who Decides When the Agent Chooses? Commercial Incentives and the Agentic Opacity of Delegated Choice**.

This repository contains synthetic decision scenarios, experimental system instructions, raw model outputs, processed analysis datasets, scripts, robustness materials, tables, figures, hashes, and documentation.

## Data Statement

The data consist only of synthetic decision scenarios and model-generated outputs. The repository contains no personal data, no human-subject data, and no data collected from human participants.

## Repository Structure

- `data/scenarios/`: locked scenarios and run plans.
- `data/raw_model_responses/`: raw model output files.
- `data/processed/`: cleaned and analysis-ready datasets.
- `experimental_materials/system_instructions/`: experimental system-instruction conditions.
- `analysis/scripts/`: analysis, scoring, validation, table and figure scripts.
- `analysis/robustness/`: robustness checks and sensitivity materials.
- `outputs/tables/`: final and supplementary tables.
- `outputs/figures/`: final and supplementary figures.
- `hashes/`: SHA-256 hashes and provenance materials.
- `docs/`: documentation, data dictionary, software versions, and file inventory.

## Reproduction Overview

Create a clean Python environment, install the required packages, inspect the locked scenarios and system instructions, parse raw model responses, score the outputs, reproduce the processed datasets, re-run analyses, regenerate tables and figures, and verify hashes.

## Basic Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
