from __future__ import annotations

import argparse
import json
from typing import Any

from src.retrieve_batch import content_bytes, validate_jsonl
from src.submit_batch import object_to_dict, utc_now
from src.submit_corrected_chunk import error_file, normalize_chunk, output_file, state_file, write_json
from src.common import path


def download_file(client: object, file_id: str, rel: str) -> int:
    target = path(rel)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content_bytes(client.files.content(file_id)))
    return validate_jsonl(rel)


def retrieve_chunk(chunk: int, client: object | None = None) -> dict[str, Any]:
    chunk = normalize_chunk(chunk)
    state_path = path(state_file(chunk))
    if not state_path.exists():
        raise SystemExit(f"chunk {chunk:02d} has no submission state.")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    batch_id = str(state.get("batch_id") or "").strip()
    if not batch_id:
        raise SystemExit(f"chunk {chunk:02d} has no batch_id.")
    if client is None:
        from openai import OpenAI

        client = OpenAI()
    batch = object_to_dict(client.batches.retrieve(batch_id))
    if batch.get("status") != "completed":
        raise SystemExit(f"chunk {chunk:02d} is not completed; status={batch.get('status')!r}.")
    output_file_id = batch.get("output_file_id")
    error_file_id = batch.get("error_file_id")
    if not output_file_id and not error_file_id:
        raise SystemExit(f"chunk {chunk:02d} has neither output_file_id nor error_file_id.")
    result: dict[str, Any] = {
        "chunk": f"{chunk:02d}",
        "batch_id": batch_id,
        "status": batch.get("status", ""),
        "output_lines": 0,
        "error_lines": 0,
    }
    if output_file_id:
        result["output_file"] = output_file(chunk)
        result["output_file_id"] = output_file_id
        result["output_lines"] = download_file(client, output_file_id, output_file(chunk))
    if error_file_id:
        result["error_file"] = error_file(chunk)
        result["error_file_id"] = error_file_id
        result["error_lines"] = download_file(client, error_file_id, error_file(chunk))
    state.update({
        "batch_status": batch.get("status", ""),
        "output_file_id": output_file_id or "",
        "error_file_id": error_file_id or "",
        "output_file": result.get("output_file", ""),
        "error_file": result.get("error_file", ""),
        "output_lines": result["output_lines"],
        "error_lines": result["error_lines"],
        "last_checked_at_utc": utc_now(),
    })
    write_json(state_file(chunk), state)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunk", required=True, type=int)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = retrieve_chunk(args.chunk)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
