from __future__ import annotations

import csv
import json
import os
import re
import time
from collections import Counter
from typing import Any

from src.common import path, write_csv, write_text
from src.retrieve_batch import content_bytes, validate_jsonl
from src.submit_batch import object_to_dict

BATCH_ID = "batch_6a42bee0c3a88190b6f498efbdba3d00"
SECRET_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}")


def scrub(obj: Any) -> Any:
    if isinstance(obj, str):
        return SECRET_PATTERN.sub("[REDACTED_OPENAI_API_KEY]", obj)
    if isinstance(obj, list):
        return [scrub(item) for item in obj]
    if isinstance(obj, dict):
        return {key: scrub(value) for key, value in obj.items()}
    return obj


def write_batch_diagnostic(batch: dict[str, Any], *, source: str) -> dict[str, Any]:
    payload = scrub(dict(batch))
    payload["diagnostic_source"] = source
    target = path("batch/batch_diagnostic.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def retrieve_batch_diagnostic(client: object, batch_id: str = BATCH_ID, delay_seconds: float = 5.0) -> dict[str, Any]:
    first = object_to_dict(client.batches.retrieve(batch_id))
    if delay_seconds > 0:
        time.sleep(delay_seconds)
    second = object_to_dict(client.batches.retrieve(batch_id))
    return write_batch_diagnostic(second, source="openai_api_second_retrieve")


def error_value(error: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = error.get(key)
        if value not in (None, ""):
            return str(value)
    return ""


def summarize_error_file(rel: str = "data/raw_api/confirmatory_batch_errors.jsonl") -> dict[str, Any]:
    target = path(rel)
    rows: list[dict[str, str]] = []
    counts: Counter[tuple[str, str, str, str]] = Counter()
    with target.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            rec = json.loads(line)
            err = rec.get("error") if isinstance(rec.get("error"), dict) else {}
            response = rec.get("response") if isinstance(rec.get("response"), dict) else {}
            code = error_value(err, "code")
            message = error_value(err, "message")
            status_code = error_value(err, "status_code") or error_value(response, "status_code")
            error_type = error_value(err, "type")
            custom_id = str(rec.get("custom_id") or "")
            counts[(code, message, status_code, error_type)] += 1
            if len(rows) < 20:
                rows.append({
                    "line_number": str(line_no),
                    "custom_id": custom_id,
                    "code": code,
                    "message": message,
                    "status_code": status_code,
                    "error_type": error_type,
                })
    count_rows = [
        {"code": code, "message": message, "status_code": status, "error_type": error_type, "count": count}
        for (code, message, status, error_type), count in counts.most_common()
    ]
    write_csv("results/tables/batch_error_counts.csv", count_rows)
    write_csv("results/tables/batch_error_examples.csv", rows)
    main = count_rows[0] if count_rows else {"code": "", "message": "", "count": 0}
    report = f"""
# Batch error diagnostic

Batch error file: `{rel}`

Error lines: {sum(counts.values())}
Main error code: {main.get('code', '')}
Main error message: {main.get('message', '')}

The first representative errors are written to `results/tables/batch_error_examples.csv`.
Grouped error counts are written to `results/tables/batch_error_counts.csv`.
"""
    write_text("reports/batch_error_diagnostic.md", report)
    return {"error_lines": sum(counts.values()), "main_error_code": main.get("code", ""), "main_error_message": main.get("message", "")}


def download_error_file(client: object, error_file_id: str) -> dict[str, Any]:
    target = path("data/raw_api/confirmatory_batch_errors.jsonl")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content_bytes(client.files.content(error_file_id)))
    validate_jsonl("data/raw_api/confirmatory_batch_errors.jsonl")
    return summarize_error_file()


def main() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        cached = path("batch/batch_status.json")
        payload: dict[str, Any] = {
            "id": BATCH_ID,
            "diagnostic_error": "OPENAI_API_KEY NOT SET",
            "api_calls_sent": 0,
        }
        if cached.exists():
            try:
                payload.update(json.loads(cached.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                payload["cached_status_error"] = "batch/batch_status.json is invalid JSON"
        write_batch_diagnostic(payload, source="cached_local_no_api_key")
        write_csv("results/tables/batch_error_counts.csv", [])
        write_csv("results/tables/batch_error_examples.csv", [])
        write_text(
            "reports/batch_error_diagnostic.md",
            "# Batch error diagnostic\n\nOPENAI_API_KEY NOT SET. Real error file was not downloaded in this environment.",
        )
        raise SystemExit("OPENAI_API_KEY NOT SET")
    from openai import OpenAI

    client = OpenAI()
    batch = retrieve_batch_diagnostic(client)
    error_file_id = batch.get("error_file_id")
    if error_file_id:
        download_error_file(client, str(error_file_id))
    print(json.dumps({
        "id": batch.get("id"),
        "status": batch.get("status"),
        "output_file_id": batch.get("output_file_id"),
        "error_file_id": batch.get("error_file_id"),
    }, indent=2))


if __name__ == "__main__":
    main()
