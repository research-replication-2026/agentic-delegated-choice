#!/usr/bin/env python3
"""T7 support script for the §5.7 "exact collection dates" marker.

Reads created_at_utc for the four analyzed batches from
confirmatory_2x2/batch/chunks_v2/submissions/chunk_0{1..4}_state.json.
These local records do not include the Batch object's own `completed_at`
field (only `last_checked_at_utc`, the last time a polling script observed
`batch_status: completed` -- an upper bound on, not the exact value of, the
true completion instant).

Per instruction, if the exact completed_at is absent locally and
OPENAI_API_KEY is set, this script would query the Batches API directly to
retrieve it. OPENAI_API_KEY is not set in this environment, so that lookup
is not attempted (no request is made) and the exact completed_at values are
reported as unavailable/BLOCKED rather than guessed.

Writes COLLECTION_DATES.md.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONF = REPO_ROOT / "confirmatory_2x2"
REPORT_PATH = Path(__file__).resolve().parent / "COLLECTION_DATES.md"

CHUNK_STATE_FILES = {
    "chunk_01": "batch/chunks_v2/submissions/chunk_01_state.json",
    "chunk_02": "batch/chunks_v2/submissions/chunk_02_state.json",
    "chunk_03": "batch/chunks_v2/submissions/chunk_03_state.json",
    "chunk_04": "batch/chunks_v2/submissions/chunk_04_state.json",
}


def main() -> None:
    api_key_present = bool(os.environ.get("OPENAI_API_KEY"))

    records = []
    for label, rel in CHUNK_STATE_FILES.items():
        state = json.loads((CONF / rel).read_text(encoding="utf-8"))
        created = datetime.fromisoformat(state["created_at_utc"])
        checked = datetime.fromisoformat(state["last_checked_at_utc"])
        records.append({
            "label": label,
            "batch_id": state["batch_id"],
            "created_at_utc": created,
            "confirmed_completed_by_utc": checked,
            "completed_at_exact": None,  # not present locally
        })

    completed_at_available_locally = any(r["completed_at_exact"] is not None for r in records)
    live_lookup_attempted = False
    live_lookup_result = None
    if not completed_at_available_locally and api_key_present:
        live_lookup_attempted = True
        try:
            import openai  # type: ignore
            client = openai.OpenAI()
            for r in records:
                b = client.batches.retrieve(r["batch_id"])
                if b.completed_at:
                    r["completed_at_exact"] = datetime.fromtimestamp(b.completed_at, tz=timezone.utc)
            live_lookup_result = "SUCCESS"
        except Exception as exc:  # pragma: no cover - only runs if a key is present
            live_lookup_result = f"FAILED: {exc}"

    lines = [
        "# COLLECTION_DATES.md",
        "",
        "Support script for the §5.7 exact-collection-dates marker.",
        "",
        f"OPENAI_API_KEY present in this environment: {api_key_present}.",
        f"Live Batches API lookup attempted: {live_lookup_attempted}"
        + (f" ({live_lookup_result})" if live_lookup_result else " (not attempted: no key present, and instructions say to query live only if a key is present)."),
        "",
        "| Chunk | Batch ID | Submitted (created_at_utc) | Confirmed completed by (last_checked_at_utc) | Exact completed_at |",
        "|---|---|---|---|---|",
    ]
    for r in records:
        exact = r["completed_at_exact"].isoformat() if r["completed_at_exact"] else "BLOCKED (not recorded locally; OPENAI_API_KEY not set, live lookup not attempted)"
        lines.append(f"| {r['label']} | {r['batch_id']} | {r['created_at_utc'].isoformat()} | {r['confirmed_completed_by_utc'].isoformat()} | {exact} |")

    first_created = min(r["created_at_utc"] for r in records)
    last_confirmed = max(r["confirmed_completed_by_utc"] for r in records)
    lines += [
        "",
        f"All four batches were submitted between {first_created.date().isoformat()} and "
        f"{max(r['created_at_utc'] for r in records).date().isoformat()} (UTC), and all four were confirmed "
        f"completed no later than {last_confirmed.isoformat()} (the last poll that observed batch_status=completed "
        "for all four; the true completion instants are somewhere between each batch's created_at_utc and this time, "
        "and in any case within the 24h completion_window).",
        "",
        "Exact `completed_at` timestamps (as returned by the OpenAI Batches API) are not preserved in the local "
        "submission-state files for these four batches and could not be retrieved live because OPENAI_API_KEY is "
        "not set in this environment. This is reported as BLOCKED rather than approximated.",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")
    print(f"api_key_present={api_key_present} live_lookup_attempted={live_lookup_attempted}")


if __name__ == "__main__":
    main()
