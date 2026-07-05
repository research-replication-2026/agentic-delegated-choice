from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from src.batch_diagnostics import summarize_error_file
from src.common import expected_action_fields, path
from src.parse_responses import parse_confirmatory_batch_output
from src.provenance import require_real_batch_data
from src import score_results, statistical_analysis


class RealBatchGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.targets = [
            path("data/raw_api/confirmatory_batch_output.jsonl"),
            path("data/raw_api/confirmatory_batch_errors.jsonl"),
            path("data/processed/confirmatory_parsed.csv"),
            path("data/processed/confirmatory_attempts_audit.csv"),
            path("data/processed/confirmatory_results.csv"),
            path("data/processed/confirmatory_results.xlsx"),
            path("data/processed/DATA_PROVENANCE.json"),
            path("batch/batch_status.json"),
            path("REAL_RESULTS_NOT_RETRIEVED.txt"),
            path("reports/batch_error_diagnostic.md"),
            path("results/tables/batch_error_counts.csv"),
            path("results/tables/batch_error_examples.csv"),
            path("results/tables/confirmatory_descriptive_analysis.csv"),
            path("results/tables/confirmatory_domain_results.csv"),
        ]
        self.backups: dict[Path, bytes | None] = {}
        for target in self.targets:
            self.backups[target] = target.read_bytes() if target.exists() else None
            if target.exists():
                target.unlink()

    def tearDown(self) -> None:
        for target, data in self.backups.items():
            if data is None:
                if target.exists():
                    target.unlink()
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)

    def first_plan_row(self) -> dict[str, str]:
        with path("data/locked/confirmatory_run_plan.csv").open("r", encoding="utf-8") as f:
            return next(csv.DictReader(f))

    def write_minimal_real_output(self) -> dict[str, str]:
        row = self.first_plan_row()
        action_level, action_prepared, confirmation_required = expected_action_fields(row["condition"])
        decision = {
            "scenario_id": row["scenario_id"],
            "condition": row["condition"],
            "selected_option_id": row["visible_partner_option_id"],
            "ranked_option_ids": [row["visible_partner_option_id"], row["visible_optimal_option_id"]],
            "criteria_used": ["rating"],
            "alternatives_presented": [row["visible_partner_option_id"], row["visible_optimal_option_id"]],
            "commercial_relationship_disclosed": False,
            "commercial_disclosure_text": "",
            "action_level": action_level,
            "action_prepared": action_prepared,
            "confirmation_required": confirmation_required,
            "short_rationale": "test",
            "simulation_only": True,
        }
        rec = {
            "id": "batch_req_test",
            "custom_id": row["observation_key"],
            "response": {
                "status_code": 200,
                "body": {
                    "model": "gpt-5.4-mini",
                    "output": [{
                        "type": "function_call",
                        "name": "submit_agentic_decision",
                        "arguments": json.dumps(decision),
                    }],
                    "usage": {"input_tokens": 10, "output_tokens": 5},
                },
            },
            "error": None,
        }
        path("data/raw_api/confirmatory_batch_output.jsonl").parent.mkdir(parents=True, exist_ok=True)
        path("data/raw_api/confirmatory_batch_output.jsonl").write_text(json.dumps(rec) + "\n", encoding="utf-8")
        path("data/raw_api/confirmatory_batch_errors.jsonl").write_text(
            json.dumps({
                "custom_id": "failed_id",
                "error": {
                    "code": "invalid_request",
                    "message": "example failure",
                    "status_code": 400,
                    "type": "invalid_request_error",
                },
            }) + "\n",
            encoding="utf-8",
        )
        path("batch/batch_status.json").write_text(
            json.dumps({"id": "batch_test", "output_file_id": "file_output_test"}) + "\n",
            encoding="utf-8",
        )
        return row

    def test_parse_real_batch_output_writes_validated_provenance_and_preserves_custom_id(self) -> None:
        row = self.write_minimal_real_output()
        result = parse_confirmatory_batch_output()
        self.assertEqual(result["http_200"], 1)
        provenance = json.loads(path("data/processed/DATA_PROVENANCE.json").read_text(encoding="utf-8"))
        self.assertEqual(provenance["source"], "real_openai_batch")
        self.assertEqual(provenance["validation_status"], "validated")
        self.assertEqual(provenance["batch_id"], "batch_test")
        with path("data/processed/confirmatory_parsed.csv").open("r", encoding="utf-8") as f:
            parsed = list(csv.DictReader(f))
        self.assertEqual(parsed[0]["observation_key"], row["observation_key"])

    def test_score_and_analysis_refuse_without_real_provenance(self) -> None:
        path("REAL_RESULTS_NOT_RETRIEVED.txt").write_text("not retrieved\n", encoding="utf-8")
        with self.assertRaises(SystemExit):
            require_real_batch_data()
        with self.assertRaises(SystemExit):
            score_results.main()
        with self.assertRaises(SystemExit):
            statistical_analysis.main()

    def test_error_diagnostic_groups_errors_and_keeps_custom_ids(self) -> None:
        self.write_minimal_real_output()
        summary = summarize_error_file()
        self.assertEqual(summary["error_lines"], 1)
        self.assertEqual(summary["main_error_code"], "invalid_request")
        examples = path("results/tables/batch_error_examples.csv").read_text(encoding="utf-8")
        self.assertIn("failed_id", examples)


if __name__ == "__main__":
    unittest.main()
