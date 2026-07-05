# Chunked resubmission plan

No API call was sent. No Batch was submitted.

## Context

The corrected full Batch `batch_6a42d4d8a18c8190910af8525e07462d` failed during validation because the organization had more than 2,000,000 pending prompt tokens for `gpt-5.4-mini`. No request was executed and no observation was produced.

## Partition

The source file is `batch/confirmatory_2000_requests_corrected_v2.jsonl`. The 2,000 requests are partitioned into four files of 500 requests each. Matched blocks are defined as `scenario_id + repetition`, and all four conditions in each matched block stay in the same chunk.

Each chunk contains 125 matched blocks and 125 requests per condition. Token counts are local estimates using `tiktoken` with `o200k_base` over request body JSON.

- Chunk 01: 683321 estimated input tokens
- Chunk 02: 683321 estimated input tokens
- Chunk 03: 683489 estimated input tokens
- Chunk 04: 683489 estimated input tokens

## Sequential Submission

Submit only one chunk at a time with `src.submit_corrected_chunk`. Chunk 02 is blocked until chunk 01 is completed, and so on. State files are isolated under `batch/chunks_v2/submissions/`.

No confirmatory analysis is allowed until all four chunks are completed, retrieved, and merged.
