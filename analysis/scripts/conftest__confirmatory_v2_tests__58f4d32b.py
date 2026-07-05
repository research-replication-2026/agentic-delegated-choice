from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session", autouse=True)
def generated_artifacts() -> None:
    modules = [
        "src.generate_scenarios",
        "src.calibrate_scenarios",
        "src.lock_confirmatory_set",
        "src.build_prompts",
        "src.validate_prompts",
        "src.run_mock",
        "src.parse_responses",
        "src.score_results",
        "src.power_simulation",
        "src.cost_estimation",
        "src.robustness_checks",
        "src.statistical_analysis",
        "src.create_figures",
        "src.create_reports",
        "src.build_batch",
        "src.create_manifest",
    ]
    for module in modules:
        subprocess.run([sys.executable, "-m", module], cwd=ROOT, check=True)
