# Who decides when the agent chooses?

Replication materials for **Who decides when the agent chooses? Platform commercial instructions in delegated selection**, revised for *Electronic Markets* (ELMA-D-26-01628).

The revised manuscript is based on **8,000 archived responses: 4,000 GPT and 4,000 Claude**, across 50 synthetic scenarios, four policies (N/S/I/C), two simulated tasks and ten repetitions. **Use [revised_8000/](revised_8000/README.md) for this manuscript.** The older 2 × 2 experiment retained elsewhere is a separate study and must not be used as the revised four-policy protocol.

## Revised study: reproduce archived analyses

The package includes exact executed requests and original response envelopes, scenarios and assignment mappings, frozen NLP v2.2.0, deidentified existing human codings, original frozen inference code, portable offline adapters, scientific reference outputs and hash/provenance checks.

```bash
python -m pip install -r revised_8000/analysis/requirements.txt
python -B revised_8000/analysis/reproduce.py
python -B revised_8000/analysis/reproduce_mechanisms.py
python -B revised_8000/analysis/check_release.py
```

No model calls or API keys are required. Reproduction preserves all 8,000 responses, five unknown selections and the distinction between initial coding agreement (**392/400; κ = 0.965**) and harmonized-record/NLP concordance (**388/400**). See [the detailed replication guide](revised_8000/README.md) for methods, dependencies, missing-outcome handling, test families, provenance and methodological limits, and [the final audit](GITHUB_REPLICATION_FINAL_AUDIT.md) for verification results and publication scope.

## Legacy experiment

The pre-existing `data/`, `analysis/`, `materials/` and most older `docs/` files primarily concern an earlier 2 × 2 experiment (neutral/commercial × recommendation/simulated preparation). They remain preserved under their original identities. Their instructions, model settings, coefficients and sample sizes must not be silently attributed to the revised N/S/I/C experiment.

The [previous root README](docs/LEGACY_README_BEFORE_REVISED_8000.md) is retained as historical documentation. The earlier [S1 materials](docs/S1_experimental_materials.md) describe that older design. For exact revised-study instructions, use the full archived [request batches](revised_8000/experimental_materials/requests/), including all scenario-specific substitutions and provider-specific formatting.

The repository verifies synthetic archived analyses; it does not establish actual consumer exposure, comprehension, transactions, welfare, internal model motives or general superiority of an implementation. The two human coding series have been checked item by item and their agreement independently recalculated: 392/400 (98.0%; Cohen's κ = 0.965). The coding control is targeted rather than representative.

## Anonymous review distribution

[Download the anonymous standalone replication ZIP](https://github.com/research-replication-2026/agentic-delegated-choice/raw/refs/heads/electronic-markets-replication-readiness-20261103/ANONYMOUS_REPLICATION_8000.zip). This distribution omits Git history, hosting-account metadata and private source-workbook identities, retains the exact scientific inputs and deidentified coding labels, and was tested independently. It contains no precomputed output dependency: the documented offline commands rebuild the results.

See [the anonymity audit](ANONYMIZATION_AUDIT.md) for whole-repository, archive, Office/PDF/image and reachable-history checks. File anonymization cannot erase GitHub ownership, public platform aliases, existing external copies or potential cross-repository links. These platform limits are stated explicitly rather than represented as an absolute non-reidentification guarantee.
