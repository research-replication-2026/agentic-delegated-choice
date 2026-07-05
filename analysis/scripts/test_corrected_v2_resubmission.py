from __future__ import annotations

import json
import os
import unittest
from pathlib import Path

from src.common import expected_action_fields, path, sha256_file
from src import resubmit_corrected_v2


class FakeResponses:
    def __init__(self, fail_on_call: int | None = None, invalid_on_call: int | None = None):
        self.fail_on_call = fail_on_call
        self.invalid_on_call = invalid_on_call
        self.calls: list[dict] = []

    def create(self, **body):
        self.calls.append(body)
        call_number = len(self.calls)
        if self.fail_on_call == call_number:
            raise RuntimeError("smoke failed")
        metadata = body["metadata"]
        condition = metadata["condition"]
        action_level, action_prepared, confirmation_required = expected_action_fields(condition)
        user_payload = json.loads(body["input"][1]["content"])
        selected = user_payload["options"][0]["option_id"]
        ranked = [option["option_id"] for option in user_payload["options"][:2]]
        decision = {
            "scenario_id": metadata["scenario_id"],
            "condition": condition,
            "selected_option_id": selected,
            "ranked_option_ids": ranked,
            "criteria_used": ["rating"],
            "alternatives_presented": ranked,
            "commercial_relationship_disclosed": False,
            "commercial_disclosure_text": "",
            "action_level": action_level,
            "action_prepared": action_prepared,
            "confirmation_required": confirmation_required,
            "short_rationale": "technical smoke test",
            "simulation_only": True,
        }
        if self.invalid_on_call == call_number:
            decision.pop("simulation_only")
        return {
            "model": body["model"],
            "output": [{
                "type": "function_call",
                "name": "submit_agentic_decision",
                "arguments": json.dumps(decision),
            }],
            "usage": {"input_tokens": 1, "output_tokens": 1},
        }


class FakeFiles:
    def __init__(self):
        self.created = 0

    def create(self, file, purpose):
        self.created += 1
        self.uploaded_bytes = file.read()
        self.purpose = purpose
        return {"id": "file_corrected_v2_mock"}


class FakeBatches:
    def __init__(self):
        self.created = 0
        self.kwargs = None

    def create(self, **kwargs):
        self.created += 1
        self.kwargs = kwargs
        return {"id": "batch_corrected_v2_mock", "status": "validating"}


class FakeClient:
    def __init__(self, responses: FakeResponses | None = None):
        self.responses = responses or FakeResponses()
        self.files = FakeFiles()
        self.batches = FakeBatches()


class CorrectedV2ResubmissionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.targets = [
            path(resubmit_corrected_v2.STATE_FILE),
            path(resubmit_corrected_v2.BATCH_ID_FILE),
            path(resubmit_corrected_v2.REGISTRY_FILE),
            path(resubmit_corrected_v2.SMOKE_OUTPUT),
            path(resubmit_corrected_v2.SMOKE_FAILURE_REPORT),
        ]
        self.backups: dict[Path, bytes | None] = {}
        for target in self.targets:
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

    def test_local_controls_pass_without_network(self) -> None:
        summary = resubmit_corrected_v2.local_controls()
        self.assertEqual(summary["issues"], [])
        self.assertEqual(summary["corrected_requests"], 2000)
        self.assertEqual(summary["unique_custom_ids"], 2000)
        self.assertEqual(summary["non_string_metadata_remaining"], 0)
        self.assertEqual(summary["smoke_requests"], 4)
        self.assertEqual(summary["smoke_uses_development_data"], "YES")

    def test_four_smoke_tests_then_single_submission(self) -> None:
        client = FakeClient()
        result = resubmit_corrected_v2.run(client, resubmit_corrected_v2.CONFIRMATION_PHRASE)
        self.assertEqual(len(client.responses.calls), 4)
        self.assertEqual(client.files.created, 1)
        self.assertEqual(client.files.purpose, "batch")
        self.assertEqual(client.batches.created, 1)
        self.assertEqual(client.batches.kwargs["endpoint"], "/v1/responses")
        self.assertEqual(client.batches.kwargs["completion_window"], "24h")
        self.assertEqual(client.batches.kwargs["metadata"]["experiment_id"], resubmit_corrected_v2.EXPERIMENT_ID)
        self.assertEqual(result["state"]["batch_id"], "batch_corrected_v2_mock")

    def test_smoke_failure_stops_before_upload(self) -> None:
        client = FakeClient(responses=FakeResponses(fail_on_call=2))
        with self.assertRaises(SystemExit):
            resubmit_corrected_v2.run(client, resubmit_corrected_v2.CONFIRMATION_PHRASE)
        self.assertEqual(len(client.responses.calls), 2)
        self.assertEqual(client.files.created, 0)
        self.assertEqual(client.batches.created, 0)
        self.assertTrue(path(resubmit_corrected_v2.SMOKE_FAILURE_REPORT).exists())

    def test_invalid_smoke_output_stops_before_upload(self) -> None:
        client = FakeClient(responses=FakeResponses(invalid_on_call=1))
        with self.assertRaises(SystemExit):
            resubmit_corrected_v2.run(client, resubmit_corrected_v2.CONFIRMATION_PHRASE)
        self.assertEqual(client.files.created, 0)
        self.assertEqual(client.batches.created, 0)

    def test_duplicate_state_blocks_before_smoke(self) -> None:
        path(resubmit_corrected_v2.STATE_FILE).parent.mkdir(parents=True, exist_ok=True)
        path(resubmit_corrected_v2.STATE_FILE).write_text(json.dumps({"batch_id": "batch_existing"}) + "\n", encoding="utf-8")
        client = FakeClient()
        with self.assertRaises(SystemExit) as cm:
            resubmit_corrected_v2.run(client, resubmit_corrected_v2.CONFIRMATION_PHRASE)
        self.assertIn("duplicate protection", str(cm.exception))
        self.assertEqual(len(client.responses.calls), 0)
        self.assertEqual(client.files.created, 0)

    def test_duplicate_sha_blocks_before_smoke(self) -> None:
        corrected_sha = sha256_file(path(resubmit_corrected_v2.CORRECTED_BATCH))
        path(resubmit_corrected_v2.REGISTRY_FILE).write_text(
            json.dumps({"submissions": [{"input_sha256": corrected_sha, "batch_id": "batch_existing_sha"}]}) + "\n",
            encoding="utf-8",
        )
        client = FakeClient()
        with self.assertRaises(SystemExit):
            resubmit_corrected_v2.run(client, resubmit_corrected_v2.CONFIRMATION_PHRASE)
        self.assertEqual(len(client.responses.calls), 0)
        self.assertEqual(client.files.created, 0)

    def test_old_failed_batch_is_preserved_and_not_confused(self) -> None:
        old_id = path("batch/LAST_BATCH_ID.txt").read_text(encoding="utf-8").strip()
        self.assertEqual(old_id, resubmit_corrected_v2.FAILED_BATCH_ID)
        client = FakeClient()
        resubmit_corrected_v2.run(client, resubmit_corrected_v2.CONFIRMATION_PHRASE)
        self.assertEqual(path("batch/LAST_BATCH_ID.txt").read_text(encoding="utf-8").strip(), old_id)
        self.assertEqual(path(resubmit_corrected_v2.BATCH_ID_FILE).read_text(encoding="utf-8").strip(), "batch_corrected_v2_mock")


if __name__ == "__main__":
    unittest.main()
