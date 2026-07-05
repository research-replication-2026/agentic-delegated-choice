from __future__ import annotations

import argparse
import json
import os
from typing import Any

from src.chunk_corrected_batch import (
    CHUNK_MANIFEST_JSON,
    ENDPOINT,
    MODEL,
    chunk_filename,
)
from src.common import path, sha256_file
from src.submit_batch import object_to_dict, utc_now

SUBMISSION_DIR = "batch/chunks_v2/submissions"
REGISTRY = "batch/chunks_v2/submissions/chunk_submission_registry.json"


def normalize_chunk(value: int | str) -> int:
    chunk = int(value)
    if chunk not in {1, 2, 3, 4}:
        raise SystemExit("--chunk must be 1, 2, 3, or 4.")
    return chunk


def chunk_label(chunk: int) -> str:
    return f"{chunk:02d}"


def state_file(chunk: int) -> str:
    return f"{SUBMISSION_DIR}/chunk_{chunk_label(chunk)}_state.json"


def batch_id_file(chunk: int) -> str:
    return f"{SUBMISSION_DIR}/chunk_{chunk_label(chunk)}_BATCH_ID.txt"


def output_file(chunk: int) -> str:
    return f"data/raw_api/chunks_v2/chunk_{chunk_label(chunk)}_output.jsonl"


def error_file(chunk: int) -> str:
    return f"data/raw_api/chunks_v2/chunk_{chunk_label(chunk)}_errors.jsonl"


def read_json(rel: str) -> dict[str, Any]:
    target = path(rel)
    if not target.exists():
        return {}
    return json.loads(target.read_text(encoding="utf-8"))


def write_json(rel: str, payload: dict[str, Any]) -> None:
    target = path(rel)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_registry() -> list[dict[str, Any]]:
    payload = read_json(REGISTRY)
    return payload.get("submissions", []) if isinstance(payload, dict) else []


def write_registry(entries: list[dict[str, Any]]) -> None:
    write_json(REGISTRY, {"submissions": entries})


def manifest_entry(chunk: int) -> dict[str, Any]:
    manifest = read_json(CHUNK_MANIFEST_JSON)
    chunk_id = chunk_label(chunk)
    for entry in manifest.get("chunks", []):
        if str(entry.get("chunk_id")) == chunk_id:
            return entry
    raise SystemExit(f"Chunk {chunk_id} is not present in manifest.")


def submitted_batch_for_sha(file_hash: str) -> str:
    for entry in read_registry():
        if entry.get("sha256") == file_hash and entry.get("batch_id"):
            return str(entry["batch_id"])
    return ""


def state_batch_id(chunk: int) -> str:
    state = read_json(state_file(chunk))
    state_batch = str(state.get("batch_id") or "").strip()
    batch_path = path(batch_id_file(chunk))
    file_batch = batch_path.read_text(encoding="utf-8").strip() if batch_path.exists() else ""
    return state_batch or file_batch


def previous_chunk_completed(chunk: int) -> bool:
    if chunk == 1:
        return True
    previous = read_json(state_file(chunk - 1))
    return previous.get("batch_status") == "completed"


def duplicate_or_sequence_error(chunk: int, file_hash: str) -> str | None:
    existing = state_batch_id(chunk)
    if existing:
        return f"chunk {chunk_label(chunk)} already has batch_id {existing}"
    submitted = submitted_batch_for_sha(file_hash)
    if submitted:
        return f"chunk file SHA-256 already submitted as {submitted}"
    state = read_json(state_file(chunk))
    if state.get("submission_in_progress") and not state.get("submission_completed"):
        return f"chunk {chunk_label(chunk)} submission is already in progress"
    if not previous_chunk_completed(chunk):
        return f"chunk {chunk_label(chunk - 1)} must be completed before chunk {chunk_label(chunk)}"
    return None


def validate_chunk_file(chunk: int) -> dict[str, Any]:
    entry = manifest_entry(chunk)
    rel = entry["filename"]
    file_hash = sha256_file(path(rel))
    if file_hash != entry["sha256"]:
        raise SystemExit(f"chunk {chunk_label(chunk)} SHA-256 mismatch: {file_hash}")
    rows = []
    with path(rel).open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    if len(rows) != 500:
        raise SystemExit(f"chunk {chunk_label(chunk)} must contain 500 requests.")
    if len({row["custom_id"] for row in rows}) != 500:
        raise SystemExit(f"chunk {chunk_label(chunk)} custom_id values are not unique.")
    if {row["url"] for row in rows} != {ENDPOINT}:
        raise SystemExit(f"chunk {chunk_label(chunk)} endpoint mismatch.")
    if {row["body"]["model"] for row in rows} != {MODEL}:
        raise SystemExit(f"chunk {chunk_label(chunk)} model mismatch.")
    return {"filename": rel, "sha256": file_hash, "request_count": len(rows)}


def submit_chunk(chunk: int, confirmation: str | None, client: object | None = None) -> dict[str, Any]:
    chunk = normalize_chunk(chunk)
    expected_confirmation = f"SUBMIT CORRECTED CHUNK {chunk_label(chunk)}"
    if confirmation != expected_confirmation:
        raise SystemExit("Confirmation failed; no chunk submitted.")
    if os.environ.get("CONFIRM_PAID_RUN") != "YES":
        raise SystemExit("CONFIRM_PAID_RUN must be YES.")
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY NOT SET")
    chunk_info = validate_chunk_file(chunk)
    block = duplicate_or_sequence_error(chunk, chunk_info["sha256"])
    if block:
        raise SystemExit(block)
    if client is None:
        from openai import OpenAI

        client = OpenAI()
    state = {
        "chunk": chunk_label(chunk),
        "submission_file": chunk_info["filename"],
        "sha256": chunk_info["sha256"],
        "request_count": chunk_info["request_count"],
        "endpoint": ENDPOINT,
        "completion_window": "24h",
        "submission_in_progress": True,
        "submission_completed": False,
        "input_file_id": "",
        "batch_id": "",
        "batch_status": "",
        "created_at_utc": utc_now(),
        "last_checked_at_utc": utc_now(),
    }
    write_json(state_file(chunk), state)
    with path(chunk_info["filename"]).open("rb") as f:
        uploaded = client.files.create(file=f, purpose="batch")
    input_file_id = object_to_dict(uploaded).get("id") or getattr(uploaded, "id", "")
    state.update({"input_file_id": input_file_id, "last_checked_at_utc": utc_now()})
    write_json(state_file(chunk), state)
    batch = client.batches.create(
        input_file_id=input_file_id,
        endpoint=ENDPOINT,
        completion_window="24h",
        metadata={
            "experiment_id": "confirmatory_2x2_corrected_v2",
            "chunk": chunk_label(chunk),
            "requests": "500",
            "sha256": chunk_info["sha256"],
        },
    )
    batch_dict = object_to_dict(batch)
    batch_id = batch_dict.get("id") or getattr(batch, "id", "")
    if not batch_id:
        raise RuntimeError("Batch creation returned no batch_id.")
    state.update({
        "batch_id": batch_id,
        "batch_status": batch_dict.get("status", ""),
        "submission_in_progress": False,
        "submission_completed": True,
        "last_checked_at_utc": utc_now(),
    })
    write_json(state_file(chunk), state)
    path(batch_id_file(chunk)).parent.mkdir(parents=True, exist_ok=True)
    path(batch_id_file(chunk)).write_text(batch_id + "\n", encoding="utf-8")
    entries = read_registry()
    entries.append({
        "chunk": chunk_label(chunk),
        "filename": chunk_info["filename"],
        "sha256": chunk_info["sha256"],
        "input_file_id": input_file_id,
        "batch_id": batch_id,
        "batch_status": state["batch_status"],
    })
    write_registry(entries)
    return state


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunk", required=True, type=int)
    parser.add_argument("--confirmation", required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    state = submit_chunk(args.chunk, args.confirmation)
    print(json.dumps({"chunk": state["chunk"], "batch_id": state["batch_id"], "status": state["batch_status"]}, indent=2))


if __name__ == "__main__":
    main()
