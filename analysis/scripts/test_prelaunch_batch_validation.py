from __future__ import annotations

import csv
import json
import re
import unittest
from collections import Counter, defaultdict

from src.common import CONDITIONS, canonical_json, path, sha256_file, sha256_text


class PrelaunchBatchValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with path("data/locked/confirmatory_run_plan.csv").open("r", encoding="utf-8") as f:
            cls.plan = list(csv.DictReader(f))
        with path("batch/confirmatory_2000_requests_corrected_v2.jsonl").open("r", encoding="utf-8") as f:
            cls.batch = [json.loads(line) for line in f if line.strip()]
        cls.schema = json.loads(path("schemas/submit_agentic_decision.json").read_text(encoding="utf-8"))

    def test_2000_requests_and_unique_custom_ids(self) -> None:
        self.assertEqual(len(self.batch), 2000)
        custom_ids = [rec["custom_id"] for rec in self.batch]
        self.assertEqual(len(custom_ids), len(set(custom_ids)))

    def test_500_observations_per_condition(self) -> None:
        self.assertEqual(Counter(row["condition"] for row in self.plan), {condition: 500 for condition in CONDITIONS})

    def test_user_prompt_identity_in_matched_blocks(self) -> None:
        by_block = defaultdict(set)
        for rec in self.batch:
            scenario_id, condition, repetition = rec["custom_id"].split("__")
            user_prompt = rec["body"]["input"][1]["content"]
            by_block[(scenario_id, repetition)].add(sha256_text(user_prompt))
        self.assertTrue(by_block)
        self.assertTrue(all(len(hashes) == 1 for hashes in by_block.values()))

    def test_tool_schema_identity(self) -> None:
        schema_hash = sha256_text(canonical_json(self.schema))
        batch_hashes = {
            sha256_text(canonical_json(rec["body"]["tools"][0]["parameters"]))
            for rec in self.batch
        }
        self.assertEqual(batch_hashes, {schema_hash})

    def test_neutral_prompts_free_of_commission_terms(self) -> None:
        forbidden = re.compile(r"commission|partenariat|partenaire|avantage économique|préférence commerciale", re.I)
        for rec in self.batch:
            if "__neutral_" in rec["custom_id"]:
                system_prompt = rec["body"]["input"][0]["content"]
                self.assertIsNone(forbidden.search(system_prompt), rec["custom_id"])

    def test_user_prompt_no_experimental_leakage(self) -> None:
        forbidden = re.compile(r"commercial_high_agenticity|commercial_low_agenticity|neutral_high_agenticity|neutral_low_agenticity|hypothesis|H1|H2|H3|experimental condition|partner option|option partenaire|commission", re.I)
        for rec in self.batch:
            user_prompt = rec["body"]["input"][1]["content"]
            self.assertIsNone(forbidden.search(user_prompt), rec["custom_id"])

    def test_agenticity_fields_and_simulation_only(self) -> None:
        for rec in self.batch:
            metadata = rec["body"]["metadata"]
            self.assertEqual(metadata["simulation_only"], "true")
            if "_high_agenticity" in rec["custom_id"]:
                self.assertEqual(metadata["expected_action_level"], "action_preparation")
                self.assertEqual(metadata["expected_action_prepared"], "true")
                self.assertEqual(metadata["expected_confirmation_required"], "true")
            else:
                self.assertEqual(metadata["expected_action_level"], "recommendation")
                self.assertEqual(metadata["expected_action_prepared"], "false")
                self.assertEqual(metadata["expected_confirmation_required"], "false")

    def test_no_api_secret_or_real_service(self) -> None:
        text = path("batch/confirmatory_2000_requests_corrected_v2.jsonl").read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"sk-[A-Za-z0-9]{20,}", text))
        self.assertIsNone(re.search(r"booking_endpoint|purchase_endpoint|checkout|stripe|paypal|transaction_url", text, re.I))
        self.assertNotIn("previous_response_id", text)

    def test_commercial_requests_identify_valid_visible_partner(self) -> None:
        plan = {row["observation_key"]: row for row in self.plan}
        placeholder = re.compile(r"\[VISIBLE_PARTNER_OPTION_ID\]|\{visible_partner_option_id\}|OPTION_PARTNER|partner_option_id|\[TAUX\]")
        commercial_seen = 0
        for rec in self.batch:
            custom_id = rec["custom_id"]
            row = plan[custom_id]
            system_prompt = rec["body"]["input"][0]["content"]
            user_payload = json.loads(rec["body"]["input"][1]["content"])
            visible_ids = {option["option_id"] for option in user_payload["options"]}
            if row["condition"].startswith("commercial_"):
                commercial_seen += 1
                self.assertIn(row["visible_partner_option_id"], system_prompt, custom_id)
                self.assertIsNone(placeholder.search(system_prompt), custom_id)
                self.assertIn(row["visible_partner_option_id"], visible_ids, custom_id)
                self.assertNotEqual(row["visible_partner_option_id"], row["visible_optimal_option_id"], custom_id)
        self.assertEqual(commercial_seen, 1000)

    def test_neutral_requests_do_not_identify_partner_or_commission(self) -> None:
        plan = {row["observation_key"]: row for row in self.plan}
        forbidden = re.compile(r"commission|partenariat|partenaire|politique commerciale|préférence commerciale", re.I)
        neutral_seen = 0
        for rec in self.batch:
            row = plan[rec["custom_id"]]
            if row["condition"].startswith("neutral_"):
                neutral_seen += 1
                system_prompt = rec["body"]["input"][0]["content"]
                self.assertIsNone(forbidden.search(system_prompt), rec["custom_id"])
                self.assertNotIn(row["visible_partner_option_id"], system_prompt, rec["custom_id"])
        self.assertEqual(neutral_seen, 1000)

    def test_commercial_pair_uses_same_visible_partner_within_block(self) -> None:
        plan = {row["observation_key"]: row for row in self.plan}
        commercial_partner_by_block = defaultdict(set)
        for rec in self.batch:
            row = plan[rec["custom_id"]]
            if row["condition"].startswith("commercial_"):
                commercial_partner_by_block[(row["scenario_id"], row["repetition"])].add(row["visible_partner_option_id"])
        self.assertEqual(len(commercial_partner_by_block), 500)
        self.assertTrue(all(len(values) == 1 for values in commercial_partner_by_block.values()))

    def test_custom_ids_match_locked_plan(self) -> None:
        self.assertEqual({rec["custom_id"] for rec in self.batch}, {row["observation_key"] for row in self.plan})

    def test_locked_scenario_and_run_plan_file_hashes_unchanged(self) -> None:
        self.assertEqual(sha256_file(path("data/locked/confirmatory_scenarios.json")), "1fd1df266514b52723d66b4c128db6bb0b2e358caabd08b824d4409d58d0cb0d")
        self.assertEqual(sha256_file(path("data/locked/confirmatory_run_plan.csv")), "35714495d2e3ed72523692c15d6d54f2eb972d26aff4f87a3cbe7bb0439fbd92")


if __name__ == "__main__":
    unittest.main()
