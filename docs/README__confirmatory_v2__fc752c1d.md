# Confirmatory V2

Autonomous local toolkit for the confirmatory 3 x 2 experiment on agentic opacity and commercial influence.

Run from `AI AGENTIC`:

```bash
PYTHONPATH=. python -m confirmatory_v2.src.generate_scenarios
PYTHONPATH=. python -m confirmatory_v2.src.calibrate_scenarios
PYTHONPATH=. python -m confirmatory_v2.src.lock_confirmatory_set
PYTHONPATH=. python -m confirmatory_v2.src.build_prompts
PYTHONPATH=. python -m confirmatory_v2.src.validate_prompts
PYTHONPATH=. python -m confirmatory_v2.src.run_mock
PYTHONPATH=. python -m confirmatory_v2.src.parse_responses
PYTHONPATH=. python -m confirmatory_v2.src.score_results
```

No real API calls are made by these scripts. Future API batches are preview-only until explicitly submitted outside this scaffold.
