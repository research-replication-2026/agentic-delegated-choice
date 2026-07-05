from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from src.build_batch import metadata_validation_errors
from src.common import CONDITIONS, path, read_csv, sha256_file, write_csv, write_json, write_text

SOURCE_BATCH = "batch/confirmatory_2000_requests_corrected_v2.jsonl"
CHUNK_DIR = "batch/chunks_v2"
CHUNK_PATTERN = "batch/chunks_v2/confirmatory_corrected_v2_chunk_{chunk:02d}.jsonl"
CHUNK_MANIFEST_CSV = "batch/chunks_v2/chunk_manifest.csv"
CHUNK_MANIFEST_JSON = "batch/chunks_v2/chunk_manifest.json"
CHUNK_HASHES = "batch/chunks_v2/CHUNK_HASHES.txt"
WAITING_MARKER = "data/processed/WAITING_FOR_ALL_4_CHUNKS.txt"
MODEL = "gpt-5.4-mini"
ENDPOINT = "/v1/responses"
SAFETY_TOKEN_LIMIT = 1_500_000
FAILED_TOKEN_BATCH_ID = "batch_6a42d4d8a18c8190910af8525e07462d"


def read_jsonl(rel: str) -> list[dict[str, Any]]:
    target = path(rel)
    with target.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(rel: str, rows: list[dict[str, Any]]) -> None:
    target = path(rel)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def block_key(record: dict[str, Any]) -> tuple[str, str]:
    metadata = record["body"]["metadata"]
    scenario_id = metadata.get("scenario_id") or record["custom_id"].split("__")[0]
    repetition = metadata.get("repetition") or record["custom_id"].split("__")[-1].replace("rep", "")
    return str(scenario_id), str(repetition)


def condition_of(record: dict[str, Any]) -> str:
    metadata = record["body"]["metadata"]
    return str(metadata.get("condition") or record["custom_id"].split("__")[1])


def source_with_indexes() -> list[dict[str, Any]]:
    rows = read_jsonl(SOURCE_BATCH)
    for index, row in enumerate(rows):
        row["_source_index"] = index
    return rows


def clean_record(record: dict[str, Any]) -> dict[str, Any]:
    clone = dict(record)
    clone.pop("_source_index", None)
    return clone


def plan_by_block() -> dict[tuple[str, str], dict[str, str]]:
    plan = read_csv("data/locked/confirmatory_run_plan.csv")
    by_block: dict[tuple[str, str], dict[str, str]] = {}
    for row in plan:
        by_block[(row["scenario_id"], str(row["repetition"]))] = row
    return by_block


def grouped_blocks(rows: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[block_key(row)].append(row)
    return grouped


def assign_blocks(rows: list[dict[str, Any]]) -> dict[tuple[str, str], int]:
    grouped = grouped_blocks(rows)
    plan = plan_by_block()
    if len(grouped) != 500:
        raise ValueError(f"Expected 500 matched blocks, got {len(grouped)}.")
    for key, block_rows in grouped.items():
        if len(block_rows) != 4:
            raise ValueError(f"Block {key} has {len(block_rows)} requests instead of 4.")
        conditions = {condition_of(row) for row in block_rows}
        if conditions != set(CONDITIONS):
            raise ValueError(f"Block {key} has conditions {sorted(conditions)}.")
    assignments: dict[tuple[str, str], int] = {}
    domain_offsets = {"hotels": 0, "software": 0, "electronics": 2}
    by_domain: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for key in grouped:
        meta = plan.get(key)
        if not meta:
            raise ValueError(f"Block {key} is not present in locked run plan.")
        by_domain[meta["domain"]].append(key)
    for domain, keys in sorted(by_domain.items()):
        offset = domain_offsets.get(domain, 0)
        keys.sort(key=lambda item: (item[0], int(item[1])))
        for index, key in enumerate(keys):
            assignments[key] = ((index + offset) % 4) + 1
    counts = Counter(assignments.values())
    if counts != {1: 125, 2: 125, 3: 125, 4: 125}:
        raise ValueError(f"Chunk block counts are not balanced: {dict(counts)}.")
    return assignments


def encoding() -> Any:
    import tiktoken

    return tiktoken.get_encoding("o200k_base")


def estimate_input_tokens(rows: list[dict[str, Any]]) -> int:
    enc = encoding()
    total = 0
    for row in rows:
        body = row.get("body", {})
        text = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        total += len(enc.encode(text))
    return total


def validate_rows(rows: list[dict[str, Any]], source_by_id: dict[str, dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if len(rows) != 2000:
        issues.append(f"source request count is {len(rows)}, expected 2000")
    custom_ids = [row["custom_id"] for row in rows]
    if len(set(custom_ids)) != len(custom_ids):
        issues.append("source custom_id values are not unique")
    if set(custom_ids) != set(source_by_id):
        issues.append("source custom_id index mismatch")
    for row in rows:
        if row.get("url") != ENDPOINT:
            issues.append(f"{row['custom_id']}: endpoint changed")
        if row.get("body", {}).get("model") != MODEL:
            issues.append(f"{row['custom_id']}: model changed")
        for issue in metadata_validation_errors(row.get("body", {}).get("metadata", {})):
            issues.append(f"{row['custom_id']}: {issue}")
    return issues


def chunk_filename(chunk_id: int) -> str:
    return CHUNK_PATTERN.format(chunk=chunk_id)


def chunk_condition_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {condition: sum(1 for row in rows if condition_of(row) == condition) for condition in CONDITIONS}


def chunk_domain_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    plan = plan_by_block()
    counts: Counter[str] = Counter()
    for key in grouped_blocks(rows):
        domain = plan[key]["domain"]
        counts[domain] += 4
    return dict(sorted(counts.items()))


def build_manifest(chunks: dict[int, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    manifest: list[dict[str, Any]] = []
    for chunk_id in range(1, 5):
        rel = chunk_filename(chunk_id)
        rows = chunks[chunk_id]
        condition_counts = chunk_condition_counts(rows)
        domain_counts = chunk_domain_counts(rows)
        tokens = estimate_input_tokens(rows)
        manifest.append({
            "chunk_id": f"{chunk_id:02d}",
            "filename": rel,
            "sha256": sha256_file(path(rel)),
            "request_count": len(rows),
            "matched_block_count": len(grouped_blocks(rows)),
            "condition_counts": json.dumps(condition_counts, sort_keys=True),
            "domain_counts": json.dumps(domain_counts, sort_keys=True),
            "estimated_input_tokens": tokens,
            "first_custom_id": rows[0]["custom_id"] if rows else "",
            "last_custom_id": rows[-1]["custom_id"] if rows else "",
        })
    return manifest


def validate_chunks(source_rows: list[dict[str, Any]], chunks: dict[int, list[dict[str, Any]]], manifest: list[dict[str, Any]]) -> dict[str, Any]:
    issues: list[str] = []
    source_clean = [clean_record(row) for row in source_rows]
    source_by_id = {row["custom_id"]: row for row in source_clean}
    issues.extend(validate_rows(source_clean, source_by_id))
    union: list[dict[str, Any]] = []
    requests_modified = 0
    for chunk_id in range(1, 5):
        rows = chunks.get(chunk_id, [])
        if len(rows) != 500:
            issues.append(f"chunk {chunk_id:02d}: expected 500 requests, got {len(rows)}")
        blocks = grouped_blocks(rows)
        if len(blocks) != 125:
            issues.append(f"chunk {chunk_id:02d}: expected 125 matched blocks, got {len(blocks)}")
        condition_counts = chunk_condition_counts(rows)
        for condition, count in condition_counts.items():
            if count != 125:
                issues.append(f"chunk {chunk_id:02d}: {condition} count is {count}, expected 125")
        for key, block_rows in blocks.items():
            if len(block_rows) != 4 or {condition_of(row) for row in block_rows} != set(CONDITIONS):
                issues.append(f"chunk {chunk_id:02d}: block {key} is split or incomplete")
        for row in rows:
            clean = clean_record(row)
            if source_by_id.get(clean["custom_id"]) != clean:
                requests_modified += 1
        union.extend(clean_record(row) for row in rows)
    union_ids = [row["custom_id"] for row in union]
    duplicate_ids = len(union_ids) - len(set(union_ids))
    missing_ids = sorted(set(source_by_id) - set(union_ids))
    added_ids = sorted(set(union_ids) - set(source_by_id))
    if len(union) != 2000:
        issues.append(f"chunk union has {len(union)} requests, expected 2000")
    if duplicate_ids:
        issues.append(f"chunk union has {duplicate_ids} duplicate custom_id values")
    if missing_ids:
        issues.append(f"missing custom_id values: {missing_ids[:5]}")
    if added_ids:
        issues.append(f"added custom_id values: {added_ids[:5]}")
    if requests_modified:
        issues.append(f"{requests_modified} requests differ from source after JSON parsing")
    token_values = [int(row["estimated_input_tokens"]) for row in manifest]
    below_limit = all(value < SAFETY_TOKEN_LIMIT for value in token_values)
    if not below_limit:
        issues.append("at least one chunk exceeds the estimated token safety limit")
    return {
        "issues": issues,
        "source_requests": len(source_rows),
        "chunks_created": len(chunks),
        "requests_per_chunk": sorted({len(rows) for rows in chunks.values()}),
        "matched_blocks_per_chunk": sorted({len(grouped_blocks(rows)) for rows in chunks.values()}),
        "requests_per_condition_per_chunk": sorted({count for rows in chunks.values() for count in chunk_condition_counts(rows).values()}),
        "all_custom_ids_preserved": "YES" if not missing_ids and not added_ids else "NO",
        "duplicate_custom_ids": duplicate_ids,
        "requests_modified": requests_modified,
        "estimated_tokens": token_values,
        "all_chunks_below_safety_limit": "YES" if below_limit else "NO",
    }


def write_reports(manifest: list[dict[str, Any]], validation: dict[str, Any]) -> None:
    token_lines = "\n".join(
        f"- Chunk {row['chunk_id']}: {row['estimated_input_tokens']} estimated input tokens"
        for row in manifest
    )
    issues = "\n".join(f"- {issue}" for issue in validation["issues"]) or "- None."
    plan = f"""
# Chunked resubmission plan

No API call was sent. No Batch was submitted.

## Context

The corrected full Batch `batch_6a42d4d8a18c8190910af8525e07462d` failed during validation because the organization had more than 2,000,000 pending prompt tokens for `gpt-5.4-mini`. No request was executed and no observation was produced.

## Partition

The source file is `{SOURCE_BATCH}`. The 2,000 requests are partitioned into four files of 500 requests each. Matched blocks are defined as `scenario_id + repetition`, and all four conditions in each matched block stay in the same chunk.

Each chunk contains 125 matched blocks and 125 requests per condition. Token counts are local estimates using `tiktoken` with `o200k_base` over request body JSON.

{token_lines}

## Sequential Submission

Submit only one chunk at a time with `src.submit_corrected_chunk`. Chunk 02 is blocked until chunk 01 is completed, and so on. State files are isolated under `batch/chunks_v2/submissions/`.

No confirmatory analysis is allowed until all four chunks are completed, retrieved, and merged.
"""
    report = f"""
# Chunked Batch validation

| Metric | Value |
| --- | --- |
| Source requests | {validation['source_requests']} |
| Chunks created | {validation['chunks_created']} |
| Requests per chunk | {validation['requests_per_chunk']} |
| Matched blocks per chunk | {validation['matched_blocks_per_chunk']} |
| Requests per condition per chunk | {validation['requests_per_condition_per_chunk']} |
| All custom IDs preserved | {validation['all_custom_ids_preserved']} |
| Duplicate custom IDs | {validation['duplicate_custom_ids']} |
| Requests modified | {validation['requests_modified']} |
| All chunks below safety limit | {validation['all_chunks_below_safety_limit']} |
| Critical failures | {len(validation['issues'])} |
| Decision | {'GO' if not validation['issues'] else 'NO-GO'} |

## Manifest

The CSV manifest is `{CHUNK_MANIFEST_CSV}` and the JSON manifest is `{CHUNK_MANIFEST_JSON}`.

## Validation Issues

{issues}
"""
    write_text("reports/chunked_resubmission_plan.md", plan)
    write_text("reports/chunked_batch_validation.md", report)


def main() -> dict[str, Any]:
    path(CHUNK_DIR).mkdir(parents=True, exist_ok=True)
    source_rows = source_with_indexes()
    assignments = assign_blocks(source_rows)
    chunks: dict[int, list[dict[str, Any]]] = {1: [], 2: [], 3: [], 4: []}
    for row in source_rows:
        chunk_id = assignments[block_key(row)]
        chunks[chunk_id].append(clean_record(row))
    for chunk_id, rows in chunks.items():
        write_jsonl(chunk_filename(chunk_id), rows)
    manifest = build_manifest(chunks)
    write_csv(CHUNK_MANIFEST_CSV, manifest)
    write_json(CHUNK_MANIFEST_JSON, {"chunks": manifest})
    write_text(CHUNK_HASHES, "\n".join(f"{row['sha256']}  {row['filename']}" for row in manifest))
    write_text(
        WAITING_MARKER,
        "Confirmatory analysis is blocked until all four corrected v2 chunks are completed, retrieved, merged, and validated.",
    )
    validation = validate_chunks(source_rows, chunks, manifest)
    write_reports(manifest, validation)
    return {"manifest": manifest, "validation": validation}


if __name__ == "__main__":
    result = main()
    print(json.dumps({
        "decision": "GO" if not result["validation"]["issues"] else "NO-GO",
        "critical_failures": len(result["validation"]["issues"]),
        "chunks_created": result["validation"]["chunks_created"],
    }, indent=2))
