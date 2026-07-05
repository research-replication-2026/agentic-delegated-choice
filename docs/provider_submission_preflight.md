# Provider submission preflight

No API call was sent. No file was uploaded. No Batch was submitted.

| Metric | Value |
| --- | --- |
| SDK available | True |
| API key detected | True |
| Submission file | batch/confirmatory_2000_requests_corrected_v2.jsonl |
| Submission SHA-256 | `5a18a98614ad5b3abe5d554ee3e6278bffe8deaaf0e33d62344bb44e3b677290` |
| Model | gpt-5.4-mini |
| Endpoint | /v1/responses |
| Requests | 2000 |
| Unique custom IDs | 2000 |
| Existing batch ID | NONE |
| Preflight tests | False |
| Critical failures | 1 |
| Decision | NO-GO |

## Critical Failures

- CONFIRM_PAID_RUN must be YES.

## Official API Shape Used

The adapter uses the OpenAI Python SDK: `client.files.create(file=..., purpose="batch")` followed by `client.batches.create(input_file_id=..., endpoint="/v1/responses", completion_window="24h", metadata=...)`.
