from __future__ import annotations

import json
import unittest

from src.build_batch import metadata_validation_errors, stringify_metadata
from src.build_corrected_batch import normalize_record_metadata
from src.common import path, sha256_file
from src.submit_batch import existing_batch_for_sha


class MetadataTypeFixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with path("batch/confirmatory_2000_requests_materialized.jsonl").open("r", encoding="utf-8") as f:
            cls.materialized = [json.loads(line) for line in f if line.strip()]
        with path("batch/confirmatory_2000_requests_corrected_v2.jsonl").open("r", encoding="utf-8") as f:
            cls.corrected = [json.loads(line) for line in f if line.strip()]

    def test_metadata_boolean_numeric_and_null_are_refused(self) -> None:
        self.assertTrue(metadata_validation_errors({"x": True}))
        self.assertTrue(metadata_validation_errors({"x": 1}))
        self.assertTrue(metadata_validation_errors({"x": 1.5}))
        self.assertTrue(metadata_validation_errors({"x": None}))

    def test_metadata_text_is_accepted(self) -> None:
        self.assertEqual(metadata_validation_errors({"x": "true", "n": "5"}), [])

    def test_metadata_conversion_true_false_and_none(self) -> None:
        converted = stringify_metadata({"t": True, "f": False, "i": 5, "d": 0.05, "s": "kept", "none": None})
        self.assertEqual(converted["t"], "true")
        self.assertEqual(converted["f"], "false")
        self.assertEqual(converted["i"], "5")
        self.assertEqual(converted["d"], "0.05")
        self.assertEqual(converted["s"], "kept")
        self.assertNotIn("none", converted)

    def test_tool_schema_booleans_remain_booleans(self) -> None:
        schema = json.loads(path("schemas/submit_agentic_decision.json").read_text(encoding="utf-8"))
        self.assertIs(schema["properties"]["simulation_only"]["const"], True)

    def test_corrected_batch_has_2000_requests_and_string_metadata(self) -> None:
        self.assertEqual(len(self.corrected), 2000)
        self.assertEqual(len({row["custom_id"] for row in self.corrected}), 2000)
        for row in self.corrected:
            metadata = row["body"]["metadata"]
            self.assertLessEqual(len(metadata), 16)
            self.assertTrue(all(isinstance(key, str) for key in metadata))
            self.assertTrue(all(isinstance(value, str) for value in metadata.values()))
            self.assertEqual(metadata_validation_errors(metadata), [])

    def test_custom_ids_and_prompts_are_unchanged(self) -> None:
        self.assertEqual([row["custom_id"] for row in self.materialized], [row["custom_id"] for row in self.corrected])
        self.assertEqual([row["body"]["input"] for row in self.materialized], [row["body"]["input"] for row in self.corrected])

    def test_only_metadata_type_normalization_changed(self) -> None:
        self.assertEqual([normalize_record_metadata(row) for row in self.materialized], self.corrected)

    def test_locked_files_unchanged(self) -> None:
        self.assertEqual(sha256_file(path("data/locked/confirmatory_scenarios.json")), "1fd1df266514b52723d66b4c128db6bb0b2e358caabd08b824d4409d58d0cb0d")
        self.assertEqual(sha256_file(path("data/locked/confirmatory_run_plan.csv")), "35714495d2e3ed72523692c15d6d54f2eb972d26aff4f87a3cbe7bb0439fbd92")

    def test_corrected_batch_token_limit_submission_is_recorded(self) -> None:
        corrected_sha = sha256_file(path("batch/confirmatory_2000_requests_corrected_v2.jsonl"))
        self.assertEqual(existing_batch_for_sha(corrected_sha), "batch_6a42d4d8a18c8190910af8525e07462d")
        self.assertTrue(path("batch/archive/failed_token_limit_batch_6a42d4d8a18c8190910af8525e07462d/FAILURE_SUMMARY.md").exists())


if __name__ == "__main__":
    unittest.main()
