# Software Versions

This file documents the software and execution environment information available in the replication package. Where the current shell differs from the original run environment, that distinction is noted.

## Observed Current Environment

- Python: `3.9.25`
- Operating system: `Linux-5.14.0-611.16.1.el9_7.x86_64-x86_64-with-glibc2.34`
- Kernel string observed during documentation preparation: `Linux proliant-4h100 5.14.0-611.16.1.el9_7.x86_64`
- R: not available in the current shell (`R: command not found`)

## Python Packages

The confirmatory requirements file lists:

```text
PyYAML>=6.0
matplotlib>=3.6
statsmodels>=0.14
openai>=2.44.0
tiktoken>=0.13.0
```

Package versions observed in the current Python environment:

| Package | Observed version |
|---|---|
| PyYAML | 6.0.3 |
| matplotlib | 3.9.4 |
| openai | 2.44.0 |
| tiktoken | 0.13.0 |
| pandas | 2.3.3 |
| numpy | 2.0.2 |
| scipy | 1.13.1 |
| statsmodels | not installed in current shell |
| openpyxl | not installed in current shell |

Because `statsmodels` is listed as a requirement but was not installed in the current shell, install dependencies in a clean environment before attempting full analysis reproduction.

## Model/API Details

Available package files indicate the confirmatory responses were generated with:

- Provider/API: OpenAI-compatible Responses API via Batch API.
- Request endpoint: `/v1/responses` in the batch request files.
- Concrete model in materialized request files: `gpt-5.4-mini`.
- Model recorded in merged response outputs and manuscript documentation: `gpt-5.4-mini-2026-03-17`.

The model configuration file uses environment variables for live execution:

- `OPENAI_MODEL`
- `OPENAI_API_KEY`

No API key is included in the replication package.

## Execution Dates

The package includes the following recorded dates:

- Confirmatory configuration creation date: `2026-06-29T00:00:00Z`.
- Manifest creation timestamp: `2026-06-29T15:24:19.907413+00:00`.
- Confirmatory batch submission window: between `2026-06-29` and `2026-06-30` UTC.
- Four confirmatory chunks were confirmed complete no later than `2026-06-30T11:29:10.892375+00:00`.

Exact `completed_at` timestamps from the live Batches API were not preserved locally in the collection-date audit and were not retrieved during documentation preparation because no API key was present.

## Reproducibility Note

The archived outputs support procedural reproduction and verification from locked scenarios, prompts, raw outputs, processing scripts, and hashes. Exact bitwise regeneration of model outputs is not guaranteed because hosted model systems and stochastic generation can change over time.
