# Corrected v2 resubmission protocol

This protocol is prepared for a later terminal run with `OPENAI_API_KEY` available. It is not executed by this preflight.

## Safety Gates

The script `src/resubmit_corrected_v2.py` performs local validation, verifies `OPENAI_API_KEY` without printing it, requires `CONFIRM_PAID_RUN=YES`, and requires the exact confirmation phrase:

`RUN 4 SMOKE TESTS THEN SUBMIT CORRECTED 2000 BATCH`

## Four Live Development Requests

The script first sends the four requests in `batch/smoke_test_4_requests_corrected_v2.jsonl` with `client.responses.create(**body)`. The file uses a development scenario only, the same tool, the same schema, the same model `gpt-5.4-mini`, the endpoint `/v1/responses`, and string-only metadata.

Smoke outputs will be written to `data/raw_api/smoke_test_corrected_v2_output.jsonl`.

If any smoke request fails, the script writes `reports/smoke_test_corrected_v2_failure.md` and stops before uploading the full Batch.

## Full Corrected Batch

Only after four valid smoke outputs, the script uploads `batch/confirmatory_2000_requests_corrected_v2.jsonl` with `purpose="batch"` and creates one Batch with `endpoint="/v1/responses"`, `completion_window="24h"`, and `experiment_id="confirmatory_2x2_corrected_v2"`.

## Duplicate Protection

The corrected submission uses distinct state files:

- `batch/submissions/confirmatory_2x2_corrected_v2_state.json`
- `batch/submissions/confirmatory_2x2_corrected_v2_BATCH_ID.txt`

It blocks if the corrected v2 state already has a `batch_id`, if the same SHA-256 is recorded in `batch/submission_registry.json`, or if a corrected v2 submission is already in progress. The old failed Batch ID remains archived and does not block this new experiment ID and new SHA.
