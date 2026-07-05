from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.common import path, sha256_file

REAL_OUTPUT = "data/raw_api/confirmatory_batch_output.jsonl"
REAL_ERRORS = "data/raw_api/confirmatory_batch_errors.jsonl"
PROVENANCE = "data/processed/DATA_PROVENANCE.json"
NOT_RETRIEVED_MARKER = "REAL_RESULTS_NOT_RETRIEVED.txt"
WAITING_FOR_CHUNKS_MARKER = "data/processed/WAITING_FOR_ALL_4_CHUNKS.txt"
REAL_SOURCE = "real_openai_batch"
VALIDATED_STATUS = "validated"


def line_count(rel: str) -> int:
    target = path(rel)
    if not target.exists():
        return 0
    with target.open("r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def marker_present() -> bool:
    return path(NOT_RETRIEVED_MARKER).exists()


def real_batch_data_error() -> str | None:
    if path(WAITING_FOR_CHUNKS_MARKER).exists():
        return "REAL BATCH DATA REQUIRED: waiting for all four corrected chunks to be completed and merged."
    if marker_present():
        return "REAL BATCH DATA REQUIRED: REAL_RESULTS_NOT_RETRIEVED.txt is present."
    prov_path = path(PROVENANCE)
    if not prov_path.exists():
        return "REAL BATCH DATA REQUIRED: DATA_PROVENANCE.json is missing."
    try:
        provenance = json.loads(prov_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return f"REAL BATCH DATA REQUIRED: DATA_PROVENANCE.json is invalid JSON: {exc}"
    if provenance.get("source") != REAL_SOURCE:
        return "REAL BATCH DATA REQUIRED: provenance source is not real_openai_batch."
    if provenance.get("validation_status") != VALIDATED_STATUS:
        return "REAL BATCH DATA REQUIRED: provenance validation_status is not validated."
    output = path(provenance.get("output_path") or REAL_OUTPUT)
    if not output.exists() or output.stat().st_size == 0:
        return "REAL BATCH DATA REQUIRED: confirmatory_batch_output.jsonl is missing or empty."
    if provenance.get("output_sha256") != sha256_file(output):
        return "REAL BATCH DATA REQUIRED: output SHA-256 does not match provenance."
    if int(provenance.get("response_count") or 0) <= 0:
        return "REAL BATCH DATA REQUIRED: no successful responses are recorded."
    return None


def require_real_batch_data() -> None:
    error = real_batch_data_error()
    if error:
        print("REAL BATCH DATA REQUIRED")
        raise SystemExit(error)


def write_validated_provenance(
    *,
    batch_id: str,
    output_file_id: str,
    response_count: int,
    error_count: int,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    output = path(REAL_OUTPUT)
    payload: dict[str, Any] = {
        "batch_id": batch_id,
        "output_file_id": output_file_id,
        "output_sha256": sha256_file(output),
        "response_count": response_count,
        "error_count": error_count,
        "source": REAL_SOURCE,
        "validation_status": VALIDATED_STATUS,
    }
    if extra:
        payload.update(extra)
    target = path(PROVENANCE)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def remove_not_retrieved_marker() -> None:
    marker = path(NOT_RETRIEVED_MARKER)
    if marker.exists():
        marker.unlink()
