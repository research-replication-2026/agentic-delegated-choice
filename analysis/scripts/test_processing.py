from __future__ import annotations

import csv
import json
from pathlib import Path

from src.common import disclosure_score

ROOT = Path(__file__).resolve().parents[1]


def rows(rel: str) -> list[dict[str, str]]:
    return list(csv.DictReader((ROOT / rel).open("r", encoding="utf-8")))


def test_recovery_after_error_and_deduplication_keys() -> None:
    scored = rows("data/processed/mock_scored.csv")
    keys = [r["observation_key"] for r in scored]
    assert len(keys) == len(set(keys))
    assert all(r["response_valid"] == "True" for r in scored)


def test_regret_calculation() -> None:
    for r in rows("data/processed/mock_scored.csv")[:50]:
        expected = round(float(r["optimal_utility"]) - float(r["selected_utility"]), 4)
        assert float(r["utility_regret"]) == expected


def test_disclosure_score() -> None:
    assert disclosure_score("", False, False) == 0
    assert disclosure_score("partner", True, False) == 1
    assert disclosure_score("commission conflict", True, False) == 2
    assert disclosure_score("10% commission conflict and possible influence", True, True) == 3


def test_action_fields_by_agenticity() -> None:
    for r in rows("data/processed/mock_scored.csv"):
        if r["agenticity"] == "A0":
            assert r["action_prepared"] == "False"
            assert r["confirmation_required"] == "False"
            assert r["action_level"] == "recommendation"
        else:
            assert r["action_prepared"] == "True"
            assert r["confirmation_required"] == "True"
            assert r["action_level"] == "booking_preparation"


def test_hashes_and_manifest_exist() -> None:
    locked = json.loads((ROOT / "data/internal/confirmatory_scenarios_locked.json").read_text(encoding="utf-8"))
    assert locked["global_hash"]
    manifest = json.loads((ROOT / "logs/manifest.json").read_text(encoding="utf-8"))
    assert manifest["no_api_calls_sent_by_pipeline"] is True
    assert any(f["path"].endswith("confirmatory_scenarios_locked.json") for f in manifest["files"])
