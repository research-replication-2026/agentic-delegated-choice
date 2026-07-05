# Materialized batch validation report

## Summary

| Metric | Value |
| --- | --- |
| OPENAI_MODEL defined | True |
| Model source file | ../data/processed/pilot_results.csv |
| Concrete model | gpt-5.4-mini |
| Original batch unchanged | YES |
| Original batch SHA-256 | `9c89339e0a3c90813528aae6f13e475597cd745359fd553ea560281e9a7b4448` |
| Materialized batch | batch/confirmatory_2000_requests_materialized.jsonl |
| Materialized batch SHA-256 | `c62d744c44e1833bd719257ef46b98b85df3fffbf36bd220dacd0faa7eee6c98` |
| JSONL rows | 2000 |
| Unique custom IDs | 2000 |
| Unresolved model placeholders | 0 |
| Distinct concrete models | 1 |
| Only body.model changed | YES |
| API secret detected | False |
| Real action possible | False |
| Critical failures | 0 |
| Decision | GO |

## Critical Failures

- None.

No API call was sent and no batch was submitted.
