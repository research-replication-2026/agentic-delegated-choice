# Corrected Batch validation report

| Metric | Value |
| --- | --- |
| Previous materialized Batch | `batch/confirmatory_2000_requests_materialized.jsonl` |
| Previous SHA-256 | `c62d744c44e1833bd719257ef46b98b85df3fffbf36bd220dacd0faa7eee6c98` |
| Corrected Batch | `batch/confirmatory_2000_requests_corrected_v2.jsonl` |
| Corrected SHA-256 | `5a18a98614ad5b3abe5d554ee3e6278bffe8deaaf0e33d62344bb44e3b677290` |
| Requests | 2000 |
| Unique custom IDs | 2000 |
| Metadata values checked | 16000 |
| Non-string metadata values remaining | 0 |
| Prompts unchanged | YES |
| Custom IDs unchanged | YES |
| Normalized files equivalent | YES |
| Locked scenarios unchanged | YES |
| Locked run plan unchanged | YES |
| Critical failures | 0 |
| Decision | GO |

The only authorized difference from the previous materialized Batch is conversion of `body.metadata` values to strings.
