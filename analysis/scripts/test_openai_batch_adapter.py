from __future__ import annotations

import json
import os
import unittest
from pathlib import Path

from src.common import path
from src import submit_batch
from src.check_batch import check_status
from src.retrieve_batch import retrieve_outputs


class FakeFiles:
    def __init__(self, upload_error: Exception | None = None, contents: dict[str, bytes] | None = None):
        self.upload_error = upload_error
        self.contents = contents or {}
        self.created = False

    def create(self, file, purpose):
        if self.upload_error:
            raise self.upload_error
        self.created = True
        assert purpose == "batch"
        return {"id": "file_mock_123"}

    def content(self, file_id):
        return self.contents[file_id]


class FakeBatches:
    def __init__(self, create_error: Exception | None = None, retrieve_payload: dict | None = None):
        self.create_error = create_error
        self.retrieve_payload = retrieve_payload or {"id": "batch_mock_123", "status": "validating"}
        self.created = False

    def create(self, **kwargs):
        if self.create_error:
            raise self.create_error
        self.created = True
        assert kwargs["endpoint"] == "/v1/responses"
        assert kwargs["completion_window"] == "24h"
        return {"id": "batch_mock_123", "status": "validating"}

    def retrieve(self, batch_id):
        payload = dict(self.retrieve_payload)
        payload.setdefault("id", batch_id)
        return payload


class FakeClient:
    def __init__(self, files: FakeFiles | None = None, batches: FakeBatches | None = None):
        self.files = files or FakeFiles()
        self.batches = batches or FakeBatches()


class OpenAIBatchAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state_paths = [
            path("batch/submission_state.json"),
            path("batch/LAST_BATCH_ID.txt"),
            path("batch/batch_status.json"),
            path("batch/submission_registry.json"),
            path("data/raw_api/confirmatory_batch_output.jsonl"),
            path("data/raw_api/confirmatory_batch_errors.jsonl"),
            path("data/processed/DATA_PROVENANCE.json"),
            path("REAL_RESULTS_NOT_RETRIEVED.txt"),
        ]
        self.backups: dict[Path, bytes | None] = {}
        for target in self.state_paths:
            self.backups[target] = target.read_bytes() if target.exists() else None
            if target.exists():
                target.unlink()
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

    def test_preflight_validation_success_with_key(self) -> None:
        summary = submit_batch.validate_submission_inputs(require_paid_guard=True, run_tests=False)
        self.assertEqual(summary["decision"], "GO")
        self.assertTrue(summary["sdk_available"])
        self.assertTrue(summary["api_key_detected"])

    def test_confirmation_argument_is_recognized(self) -> None:
        args = submit_batch.build_parser().parse_args([
            "--confirmation",
            submit_batch.CONFIRMATION_PHRASE,
        ])
        self.assertEqual(args.confirmation, submit_batch.CONFIRMATION_PHRASE)
        self.assertFalse(args.preflight)

    def test_preflight_argument_is_still_recognized(self) -> None:
        args = submit_batch.build_parser().parse_args(["--preflight"])
        self.assertTrue(args.preflight)
        self.assertIsNone(args.confirmation)

    def test_successful_upload_and_batch_creation(self) -> None:
        state = submit_batch.submit(client=FakeClient(), confirmation=submit_batch.CONFIRMATION_PHRASE, run_tests=False)
        self.assertEqual(state["input_file_id"], "file_mock_123")
        self.assertEqual(state["batch_id"], "batch_mock_123")
        self.assertTrue(path("batch/LAST_BATCH_ID.txt").exists())

    def test_upload_error_is_persisted(self) -> None:
        with self.assertRaises(RuntimeError):
            submit_batch.submit(client=FakeClient(files=FakeFiles(upload_error=RuntimeError("upload failed"))), confirmation=submit_batch.CONFIRMATION_PHRASE, run_tests=False)
        state = json.loads(path("batch/submission_state.json").read_text(encoding="utf-8"))
        self.assertIn("upload failed", state["error"])
        self.assertEqual(state["input_file_id"], "")

    def test_create_error_after_upload_preserves_input_file_id(self) -> None:
        with self.assertRaises(RuntimeError):
            submit_batch.submit(client=FakeClient(batches=FakeBatches(create_error=RuntimeError("create failed"))), confirmation=submit_batch.CONFIRMATION_PHRASE, run_tests=False)
        state = json.loads(path("batch/submission_state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["input_file_id"], "file_mock_123")
        self.assertIn("create failed", state["error"])

    def test_duplicate_file_hash_blocks_submission(self) -> None:
        file_hash = submit_batch.sha256_file(path(submit_batch.SUBMISSION_BATCH))
        path("batch/submission_registry.json").write_text(json.dumps({"submissions": [{"input_sha256": file_hash, "batch_id": "batch_existing"}]}) + "\n", encoding="utf-8")
        summary = submit_batch.validate_submission_inputs(require_paid_guard=True, run_tests=False)
        self.assertEqual(summary["decision"], "NO-GO")
        self.assertTrue(any("FILE SHA-256 ALREADY SUBMITTED" in item for item in summary["critical"]))

    def test_bad_hash_blocks_preflight(self) -> None:
        old = submit_batch.EXPECTED_SHA256
        submit_batch.EXPECTED_SHA256 = "bad"
        try:
            summary = submit_batch.validate_submission_inputs(require_paid_guard=True, run_tests=False)
            self.assertEqual(summary["decision"], "NO-GO")
            self.assertTrue(any("SHA-256 mismatch" in item for item in summary["critical"]))
        finally:
            submit_batch.EXPECTED_SHA256 = old

    def test_bad_request_count_url_and_model_block_preflight(self) -> None:
        target = path("batch/test_bad_submission.jsonl")
        target.write_text(json.dumps({"custom_id": "x", "url": "/bad", "body": {"model": "bad"}}) + "\n", encoding="utf-8")
        old_file = submit_batch.SUBMISSION_BATCH
        old_hash = submit_batch.EXPECTED_SHA256
        submit_batch.SUBMISSION_BATCH = "batch/test_bad_submission.jsonl"
        submit_batch.EXPECTED_SHA256 = submit_batch.sha256_file(target)
        try:
            summary = submit_batch.validate_submission_inputs(require_paid_guard=True, run_tests=False)
            self.assertEqual(summary["decision"], "NO-GO")
            joined = "\n".join(summary["critical"])
            self.assertIn("Expected 2000 requests", joined)
            self.assertIn("URLs", joined)
            self.assertIn("body.model", joined)
        finally:
            submit_batch.SUBMISSION_BATCH = old_file
            submit_batch.EXPECTED_SHA256 = old_hash
            target.unlink()

    def test_missing_api_key_blocks_preflight(self) -> None:
        os.environ.pop("OPENAI_API_KEY", None)
        summary = submit_batch.validate_submission_inputs(require_paid_guard=True, run_tests=False)
        self.assertEqual(summary["decision"], "NO-GO")
        self.assertIn("OPENAI_API_KEY NOT SET", summary["critical"])

    def test_missing_api_key_blocks_submit_without_prompt_or_network(self) -> None:
        os.environ.pop("OPENAI_API_KEY", None)
        client = FakeClient()
        with self.assertRaises(SystemExit) as cm:
            submit_batch.submit(client=client, confirmation=submit_batch.CONFIRMATION_PHRASE, run_tests=False)
        self.assertEqual(str(cm.exception), "OPENAI_API_KEY NOT SET")
        self.assertFalse(client.files.created)
        self.assertFalse(client.batches.created)

    def test_missing_paid_guard_blocks_submit_before_network(self) -> None:
        os.environ.pop("CONFIRM_PAID_RUN", None)
        client = FakeClient()
        with self.assertRaises(SystemExit) as cm:
            submit_batch.submit(client=client, confirmation=submit_batch.CONFIRMATION_PHRASE, run_tests=False)
        self.assertIn("CONFIRM_PAID_RUN must be YES.", str(cm.exception))
        self.assertFalse(client.files.created)
        self.assertFalse(client.batches.created)

    def test_wrong_confirmation_blocks_before_network(self) -> None:
        client = FakeClient()
        with self.assertRaises(SystemExit) as cm:
            submit_batch.submit(client=client, confirmation="NO", run_tests=False)
        self.assertIn("Confirmation failed", str(cm.exception))
        self.assertFalse(client.files.created)
        self.assertFalse(client.batches.created)

    def test_missing_confirmation_blocks_before_network(self) -> None:
        client = FakeClient()
        with self.assertRaises(SystemExit) as cm:
            submit_batch.submit(client=client, run_tests=False)
        self.assertIn("Confirmation failed", str(cm.exception))
        self.assertFalse(client.files.created)
        self.assertFalse(client.batches.created)

    def test_duplicate_file_hash_blocks_submit_before_network(self) -> None:
        file_hash = submit_batch.sha256_file(path(submit_batch.SUBMISSION_BATCH))
        path("batch/submission_registry.json").write_text(json.dumps({"submissions": [{"input_sha256": file_hash, "batch_id": "batch_existing"}]}) + "\n", encoding="utf-8")
        client = FakeClient()
        with self.assertRaises(SystemExit) as cm:
            submit_batch.submit(client=client, confirmation=submit_batch.CONFIRMATION_PHRASE, run_tests=False)
        self.assertIn("FILE SHA-256 ALREADY SUBMITTED", str(cm.exception))
        self.assertFalse(client.files.created)
        self.assertFalse(client.batches.created)

    def test_check_batch_status_updates_state(self) -> None:
        path("batch/LAST_BATCH_ID.txt").write_text("batch_mock_123\n", encoding="utf-8")
        result = check_status(FakeClient(batches=FakeBatches(retrieve_payload={"id": "batch_mock_123", "status": "in_progress"})))
        self.assertEqual(result["status"], "in_progress")
        state = json.loads(path("batch/submission_state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["batch_status"], "in_progress")

    def test_retrieve_outputs_and_errors(self) -> None:
        path("batch/submission_state.json").write_text(json.dumps({"batch_id": "batch_mock_123", "batch_status": "completed"}) + "\n", encoding="utf-8")
        client = FakeClient(
            files=FakeFiles(contents={
                "out_file": b'{"custom_id":"x","response":{"status_code":200,"body":{"output":[]}}}\n',
                "err_file": b'{"custom_id":"bad","error":{"code":"bad_request","message":"bad","status_code":400,"type":"invalid_request_error"}}\n',
            }),
            batches=FakeBatches(retrieve_payload={
                "id": "batch_mock_123",
                "status": "completed",
                "output_file_id": "out_file",
                "error_file_id": "err_file",
                "request_counts": {"total": 2, "completed": 1, "failed": 1},
            }),
        )
        result = retrieve_outputs(client)
        self.assertIn("output", result)
        self.assertIn("errors", result)
        self.assertEqual(result["successful_responses"], "1")
        self.assertIn("custom_id", path("data/raw_api/confirmatory_batch_output.jsonl").read_text(encoding="utf-8"))
        self.assertIn("custom_id", path("data/raw_api/confirmatory_batch_errors.jsonl").read_text(encoding="utf-8"))

    def test_completed_batch_without_output_file_downloads_errors_and_fails(self) -> None:
        path("batch/submission_state.json").write_text(json.dumps({"batch_id": "batch_mock_123", "batch_status": "completed"}) + "\n", encoding="utf-8")
        client = FakeClient(
            files=FakeFiles(contents={
                "err_file": b'{"custom_id":"bad","error":{"code":"invalid","message":"failed","status_code":400,"type":"invalid_request_error"}}\n',
            }),
            batches=FakeBatches(retrieve_payload={
                "id": "batch_mock_123",
                "status": "completed",
                "output_file_id": None,
                "error_file_id": "err_file",
                "request_counts": {"total": 2000, "completed": 0, "failed": 2000},
            }),
        )
        with self.assertRaises(SystemExit) as cm:
            retrieve_outputs(client)
        self.assertIn("Completed batch has no output_file_id", str(cm.exception))
        self.assertTrue(path("data/raw_api/confirmatory_batch_errors.jsonl").exists())

    def test_total_request_failure_without_successes_fails(self) -> None:
        path("batch/submission_state.json").write_text(json.dumps({"batch_id": "batch_mock_123", "batch_status": "completed"}) + "\n", encoding="utf-8")
        client = FakeClient(
            files=FakeFiles(contents={
                "out_file": b'{"custom_id":"bad","response":{"status_code":400,"body":{}}}\n',
            }),
            batches=FakeBatches(retrieve_payload={
                "id": "batch_mock_123",
                "status": "completed",
                "output_file_id": "out_file",
                "error_file_id": None,
                "request_counts": {"total": 1, "completed": 0, "failed": 1},
            }),
        )
        with self.assertRaises(SystemExit) as cm:
            retrieve_outputs(client)
        self.assertIn("No successful HTTP 200 responses", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
