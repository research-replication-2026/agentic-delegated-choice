from __future__ import annotations

import json
from typing import Any

from src.chunk_corrected_batch import SOURCE_BATCH, WAITING_MARKER, read_jsonl
from src.common import CONDITIONS, path, sha256_file, write_json
from src.submit_corrected_chunk import error_file, output_file, state_file
from src.provenance import NOT_RETRIEVED_MARKER

MERGED_OUTPUT = "data/raw_api/confirmatory_corrected_v2_merged_output.jsonl"
MERGED_ERRORS = "data/raw_api/confirmatory_corrected_v2_merged_errors.jsonl"
PROVENANCE = "data/processed/DATA_PROVENANCE.json"


def read_state(chunk: int) -> dict[str, Any]:
    state_path = path(state_file(chunk))
    if not state_path.exists():
        raise SystemExit(f"chunk {chunk:02d} state is missing.")
    return json.loads(state_path.read_text(encoding="utf-8"))


def read_jsonl_if_exists(rel: str) -> list[dict[str, Any]]:
    target = path(rel)
    if not target.exists():
        return []
    with target.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def row_custom_id(row: dict[str, Any]) -> str:
    return str(row.get("custom_id") or "")


def write_rows(rel: str, rows: list[dict[str, Any]]) -> None:
    target = path(rel)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def merge_outputs() -> dict[str, Any]:
    source = read_jsonl(SOURCE_BATCH)
    source_ids = [row["custom_id"] for row in source]
    source_set = set(source_ids)
    output_by_id: dict[str, dict[str, Any]] = {}
    error_by_id: dict[str, dict[str, Any]] = {}
    batch_ids: list[str] = []
    for chunk in range(1, 5):
        state = read_state(chunk)
        if state.get("batch_status") != "completed":
            raise SystemExit(f"chunk {chunk:02d} is not completed.")
        if not state.get("batch_id"):
            raise SystemExit(f"chunk {chunk:02d} has no batch_id.")
        batch_ids.append(str(state["batch_id"]))
        outputs = read_jsonl_if_exists(output_file(chunk))
        errors = read_jsonl_if_exists(error_file(chunk))
        if not outputs and not errors:
            raise SystemExit(f"chunk {chunk:02d} has no downloaded output or error file.")
        for row in outputs:
            custom_id = row_custom_id(row)
            if custom_id in output_by_id or custom_id in error_by_id:
                raise SystemExit(f"duplicate custom_id in merged chunk files: {custom_id}")
            output_by_id[custom_id] = row
        for row in errors:
            custom_id = row_custom_id(row)
            if custom_id in output_by_id or custom_id in error_by_id:
                raise SystemExit(f"duplicate custom_id in merged chunk files: {custom_id}")
            error_by_id[custom_id] = row
    merged_ids = set(output_by_id) | set(error_by_id)
    missing = sorted(source_set - merged_ids)
    extra = sorted(merged_ids - source_set)
    if missing:
        raise SystemExit(f"missing custom_id values after merge: {missing[:5]}")
    if extra:
        raise SystemExit(f"unexpected custom_id values after merge: {extra[:5]}")
    if len(merged_ids) != 2000:
        raise SystemExit(f"expected 2000 unique custom_id values after merge, got {len(merged_ids)}")
    conditions = {condition: 0 for condition in CONDITIONS}
    for custom_id in merged_ids:
        parts = custom_id.split("__")
        if len(parts) >= 2 and parts[1] in conditions:
            conditions[parts[1]] += 1
    if conditions != {condition: 500 for condition in CONDITIONS}:
        raise SystemExit(f"condition coverage mismatch after merge: {conditions}")
    ordered_outputs = [output_by_id[custom_id] for custom_id in source_ids if custom_id in output_by_id]
    ordered_errors = [error_by_id[custom_id] for custom_id in source_ids if custom_id in error_by_id]
    write_rows(MERGED_OUTPUT, ordered_outputs)
    write_rows(MERGED_ERRORS, ordered_errors)
    provenance = {
        "source": "real_openai_batch",
        "collection_mode": "chunked_corrected_v2",
        "validation_status": "validated",
        "output_path": MERGED_OUTPUT,
        "error_path": MERGED_ERRORS,
        "output_sha256": sha256_file(path(MERGED_OUTPUT)),
        "error_sha256": sha256_file(path(MERGED_ERRORS)) if path(MERGED_ERRORS).exists() else "",
        "response_count": len(ordered_outputs),
        "error_count": len(ordered_errors),
        "expected_request_count": 2000,
        "unique_custom_ids": len(merged_ids),
        "batch_ids": batch_ids,
        "condition_counts": conditions,
    }
    write_json(PROVENANCE, provenance)
    for rel in [WAITING_MARKER, NOT_RETRIEVED_MARKER]:
        marker = path(rel)
        if marker.exists():
            marker.unlink()
    return provenance


def main() -> None:
    provenance = merge_outputs()
    print(json.dumps({
        "response_count": provenance["response_count"],
        "error_count": provenance["error_count"],
        "unique_custom_ids": provenance["unique_custom_ids"],
    }, indent=2))


if __name__ == "__main__":
    main()
