from __future__ import annotations

import json

from src.common import path
from src.submit_batch import LAST_BATCH_ID, STATE_FILE, atomic_write_json, load_state, object_to_dict, utc_now


def check_status(client: object | None = None) -> dict:
    batch_id_path = path(LAST_BATCH_ID)
    if not batch_id_path.exists():
        raise SystemExit("No batch ID recorded.")
    batch_id = batch_id_path.read_text(encoding="utf-8").strip()
    if not batch_id:
        raise SystemExit("Recorded batch ID is empty.")
    if client is None:
        from openai import OpenAI
        client = OpenAI()
    batch = client.batches.retrieve(batch_id)
    batch_dict = object_to_dict(batch)
    path("batch/batch_status.json").write_text(json.dumps(batch_dict, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    state = load_state()
    state.update({
        "batch_id": batch_id,
        "batch_status": batch_dict.get("status", ""),
        "last_checked_at_utc": utc_now(),
    })
    atomic_write_json(STATE_FILE, state)
    return batch_dict


def main() -> None:
    batch = check_status()
    print(json.dumps({"batch_id": batch.get("id", ""), "status": batch.get("status", "")}, indent=2))


if __name__ == "__main__":
    main()
