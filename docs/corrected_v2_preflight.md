# Corrected v2 preflight

No API call was sent. No Batch was submitted.

## First Batch Failure

- Failed Batch ID: `batch_6a42bee0c3a88190b6f498efbdba3d00`
- Successful requests: 0
- Failed requests: 2000
- Root cause: Invalid type for 'metadata.expected_action_prepared': expected a string, but got a boolean instead.

## Metadata Correction

Only `body.metadata` values were changed. Boolean values are now strings (`true` / `false`), numeric values are stable strings, existing strings are unchanged, and `None` values are omitted.

- Previous materialized SHA-256: `c62d744c44e1833bd719257ef46b98b85df3fffbf36bd220dacd0faa7eee6c98`
- Corrected Batch: `batch/confirmatory_2000_requests_corrected_v2.jsonl`
- Corrected SHA-256: `5a18a98614ad5b3abe5d554ee3e6278bffe8deaaf0e33d62344bb44e3b677290`
- Metadata values converted: 6000
- Metadata values checked: 16000
- Non-string metadata remaining: 0
- Prompts unchanged: YES
- Custom IDs unchanged: YES
- Locked scenarios unchanged: YES
- Locked run plan unchanged: YES

## Smoke Test File

- Smoke test file: `batch/smoke_test_4_requests_corrected_v2.jsonl`
- Requests: 4
- Uses development data: YES
