from __future__ import annotations

import json
import os
import unittest
from collections import Counter, defaultdict
from pathlib import Path

from src.chunk_corrected_batch import (
    CHUNK_MANIFEST_JSON,
    CONDITIONS,
    SAFETY_TOKEN_LIMIT,
    SOURCE_BATCH,
    WAITING_MARKER,
    chunk_filename,
    estimate_input_tokens,
    grouped_blocks,
    main as build_chunks,
    read_jsonl,
)
from src.common import path, sha256_file
from src.merge_corrected_chunk_outputs import MERGED_ERRORS, MERGED_OUTPUT, PROVENANCE, merge_outputs
from src.provenance import require_real_batch_data
from src.submit_corrected_chunk import (
    REGISTRY,
    batch_id_file,
    state_file,
    submit_chunk,
    write_json,
)


class FakeFiles:
    def __init__(self):
        self.created = 0

    def create(self, file, purpose):
        self.created += 1
        self.purpose = purpose
        self.uploaded = file.read()
        return {"id": "file_chunk_mock"}


class FakeBatches:
    def __init__(self):
        self.created = 0

    def create(self, **kwargs):
        self.created += 1
        self.kwargs = kwargs
        return {"id": "batch_chunk_mock", "status": "validating"}


class FakeClient:
    def __init__(self):
        self.files = FakeFiles()
        self.batches = FakeBatches()


class ChunkedResubmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        build_chunks()
        cls.source = read_jsonl(SOURCE_BATCH)
        cls.source_by_id = {row["custom_id"]: row for row in cls.source}
        cls.chunks = {
            chunk: read_jsonl(chunk_filename(chunk))
            for chunk in range(1, 5)
        }

    def setUp(self) -> None:
        self.targets = [
            path(REGISTRY),
            path(MERGED_OUTPUT),
            path(MERGED_ERRORS),
            path(PROVENANCE),
            path(WAITING_MARKER),
            path("REAL_RESULTS_NOT_RETRIEVED.txt"),
        ]
        for chunk in range(1, 5):
            self.targets.extend([
                path(state_file(chunk)),
                path(batch_id_file(chunk)),
                path(f"data/raw_api/chunks_v2/chunk_{chunk:02d}_output.jsonl"),
                path(f"data/raw_api/chunks_v2/chunk_{chunk:02d}_errors.jsonl"),
            ])
        self.backups: dict[Path, bytes | None] = {}
        for target in self.targets:
            self.backups[target] = target.read_bytes() if target.exists() else None
        self.old_env = dict(os.environ)
        os.environ["OPENAI_API_KEY"] = "test-key-not-real"
        os.environ["CONFIRM_PAID_RUN"] = "YES"

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self.old_env)
        for target, data in self.backups.items():
            if data is None:
                if target.exists():
                    target.unlink()
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)

    def test_four_chunk_files_and_counts(self) -> None:
        self.assertEqual(len(self.chunks), 4)
        for chunk, rows in self.chunks.items():
            self.assertEqual(len(rows), 500, chunk)
            self.assertEqual(len({row["custom_id"] for row in rows}), 500)

    def test_125_requests_per_condition_and_blocks_per_chunk(self) -> None:
        for rows in self.chunks.values():
            conditions = Counter(row["body"]["metadata"]["condition"] for row in rows)
            self.assertEqual(conditions, {condition: 125 for condition in CONDITIONS})
            blocks = grouped_blocks(rows)
            self.assertEqual(len(blocks), 125)
            for block_rows in blocks.values():
                self.assertEqual(len(block_rows), 4)
                self.assertEqual({row["body"]["metadata"]["condition"] for row in block_rows}, set(CONDITIONS))

    def test_union_exact_custom_ids_and_no_request_modification(self) -> None:
        union = [row for rows in self.chunks.values() for row in rows]
        union_ids = [row["custom_id"] for row in union]
        self.assertEqual(len(union_ids), 2000)
        self.assertEqual(len(set(union_ids)), 2000)
        self.assertEqual(set(union_ids), set(self.source_by_id))
        modified = sum(1 for row in union if self.source_by_id[row["custom_id"]] != row)
        self.assertEqual(modified, 0)

    def test_token_estimates_are_below_limit(self) -> None:
        manifest = json.loads(path(CHUNK_MANIFEST_JSON).read_text(encoding="utf-8"))["chunks"]
        self.assertEqual(len(manifest), 4)
        for entry in manifest:
            estimated = int(entry["estimated_input_tokens"])
            self.assertGreater(estimated, 0)
            self.assertLess(estimated, SAFETY_TOKEN_LIMIT)
            chunk = int(entry["chunk_id"])
            self.assertEqual(estimate_input_tokens(self.chunks[chunk]), estimated)

    def test_next_chunk_blocked_until_previous_completed(self) -> None:
        client = FakeClient()
        with self.assertRaises(SystemExit) as cm:
            submit_chunk(2, "SUBMIT CORRECTED CHUNK 02", client=client)
        self.assertIn("chunk 01 must be completed", str(cm.exception))
        self.assertEqual(client.files.created, 0)
        self.assertEqual(client.batches.created, 0)

    def test_duplicate_hash_blocks_submission(self) -> None:
        chunk_hash = sha256_file(path(chunk_filename(1)))
        path(REGISTRY).parent.mkdir(parents=True, exist_ok=True)
        path(REGISTRY).write_text(
            json.dumps({"submissions": [{"sha256": chunk_hash, "batch_id": "batch_existing"}]}) + "\n",
            encoding="utf-8",
        )
        client = FakeClient()
        with self.assertRaises(SystemExit) as cm:
            submit_chunk(1, "SUBMIT CORRECTED CHUNK 01", client=client)
        self.assertIn("already submitted", str(cm.exception))
        self.assertEqual(client.files.created, 0)

    def test_chunk_one_single_batch_api_submission_with_fake_client(self) -> None:
        client = FakeClient()
        state = submit_chunk(1, "SUBMIT CORRECTED CHUNK 01", client=client)
        self.assertEqual(client.files.created, 1)
        self.assertEqual(client.files.purpose, "batch")
        self.assertEqual(client.batches.created, 1)
        self.assertEqual(client.batches.kwargs["endpoint"], "/v1/responses")
        self.assertEqual(client.batches.kwargs["completion_window"], "24h")
        self.assertEqual(state["batch_id"], "batch_chunk_mock")

    def test_analysis_refuses_before_fusion_complete(self) -> None:
        path(WAITING_MARKER).parent.mkdir(parents=True, exist_ok=True)
        path(WAITING_MARKER).write_text("waiting\n", encoding="utf-8")
        with self.assertRaises(SystemExit):
            require_real_batch_data()

    def test_merge_by_custom_id_after_all_chunks(self) -> None:
        source_order = [row["custom_id"] for row in self.source]
        for chunk in range(1, 5):
            write_json(state_file(chunk), {"batch_status": "completed", "batch_id": f"batch_chunk_{chunk:02d}"})
            output_path = path(f"data/raw_api/chunks_v2/chunk_{chunk:02d}_output.jsonl")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open("w", encoding="utf-8") as f:
                for row in reversed(self.chunks[chunk]):
                    f.write(json.dumps({"custom_id": row["custom_id"], "response": {"status_code": 200}}) + "\n")
        path(WAITING_MARKER).parent.mkdir(parents=True, exist_ok=True)
        path(WAITING_MARKER).write_text("waiting\n", encoding="utf-8")
        provenance = merge_outputs()
        self.assertEqual(provenance["response_count"], 2000)
        self.assertEqual(provenance["error_count"], 0)
        merged = read_jsonl(MERGED_OUTPUT)
        self.assertEqual([row["custom_id"] for row in merged], source_order)
        self.assertFalse(path(WAITING_MARKER).exists())

    def test_failed_batches_are_preserved(self) -> None:
        self.assertTrue(path("batch/archive/failed_batch_6a42bee0c3a88190b6f498efbdba3d00/FAILURE_SUMMARY.md").exists())
        self.assertTrue(path("batch/archive/failed_token_limit_batch_6a42d4d8a18c8190910af8525e07462d/FAILURE_SUMMARY.md").exists())


if __name__ == "__main__":
    unittest.main()
