from __future__ import annotations

import json
from typing import Any

from src.common import path
from src.provenance import REAL_ERRORS, REAL_OUTPUT, remove_not_retrieved_marker
from src.submit_batch import load_state, object_to_dict


def content_bytes(content: Any) -> bytes:
    if isinstance(content, bytes):
        return content
    if isinstance(content, str):
        return content.encode("utf-8")
    if hasattr(content, "read"):
        data = content.read()
        return data if isinstance(data, bytes) else str(data).encode("utf-8")
    if hasattr(content, "content"):
        data = content.content
        return data if isinstance(data, bytes) else str(data).encode("utf-8")
    return str(content).encode("utf-8")


def request_counts(batch: dict[str, Any]) -> dict[str, int]:
    counts = batch.get("request_counts") or {}
    return {
        "total": int(counts.get("total") or 0),
        "completed": int(counts.get("completed") or 0),
        "failed": int(counts.get("failed") or 0),
    }


def validate_jsonl(rel: str) -> int:
    target = path(rel)
    count = 0
    with target.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{rel} line {line_no} is not valid JSON: {exc}") from exc
            count += 1
    return count


def count_successful_responses(rel: str) -> int:
    target = path(rel)
    successes = 0
    with target.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            response = rec.get("response") or {}
            if int(response.get("status_code") or 0) == 200:
                successes += 1
    return successes


def download_file(client: object, file_id: str, rel: str) -> int:
    target = path(rel)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content_bytes(client.files.content(file_id)))
    return validate_jsonl(rel)


def retrieve_outputs(client: object | None = None) -> dict[str, str]:
    state = load_state()
    batch_id = state.get("batch_id", "")
    status = state.get("batch_status", "")
    if not batch_id:
        raise SystemExit("No batch ID recorded.")
    if status != "completed":
        raise SystemExit(f"Batch is not completed; current status is {status!r}.")
    if client is None:
        from openai import OpenAI
        client = OpenAI()
    batch = object_to_dict(client.batches.retrieve(batch_id))
    if batch.get("status") != "completed":
        raise SystemExit(f"Provider status is not completed; current status is {batch.get('status')!r}.")
    counts = request_counts(batch)
    print(f"request_counts.total: {counts['total']}")
    print(f"request_counts.completed: {counts['completed']}")
    print(f"request_counts.failed: {counts['failed']}")
    output_file_id = batch.get("output_file_id")
    error_file_id = batch.get("error_file_id")
    result = {
        "request_counts.total": str(counts["total"]),
        "request_counts.completed": str(counts["completed"]),
        "request_counts.failed": str(counts["failed"]),
    }
    if error_file_id:
        error_lines = download_file(client, error_file_id, REAL_ERRORS)
        result["errors"] = str(path(REAL_ERRORS))
        result["error_lines"] = str(error_lines)
    if not output_file_id:
        raise SystemExit("Completed batch has no output_file_id.")
    output_lines = download_file(client, output_file_id, REAL_OUTPUT)
    successes = count_successful_responses(REAL_OUTPUT)
    if successes <= 0:
        raise SystemExit("No successful HTTP 200 responses are available.")
    remove_not_retrieved_marker()
    result["output"] = str(path(REAL_OUTPUT))
    result["output_lines"] = str(output_lines)
    result["successful_responses"] = str(successes)
    return result


def main() -> None:
    result = retrieve_outputs()
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
