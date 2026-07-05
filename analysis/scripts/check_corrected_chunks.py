from __future__ import annotations

import argparse
import json
from typing import Any

from src.common import path
from src.submit_batch import object_to_dict, utc_now
from src.submit_corrected_chunk import normalize_chunk, state_file, write_json


def check_chunk(chunk: int, client: object | None = None) -> dict[str, Any]:
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
    state.update({
        "batch_status": batch.get("status", ""),
        "output_file_id": batch.get("output_file_id", ""),
        "error_file_id": batch.get("error_file_id", ""),
        "request_counts": batch.get("request_counts", {}),
        "last_checked_at_utc": utc_now(),
    })
    write_json(state_file(chunk), state)
    return state


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunk", type=int)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    chunks = [normalize_chunk(args.chunk)] if args.chunk else [1, 2, 3, 4]
    states = [check_chunk(chunk) for chunk in chunks]
    print(json.dumps(states, indent=2))


if __name__ == "__main__":
    main()
