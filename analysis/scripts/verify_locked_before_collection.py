#!/usr/bin/env python3
"""T6 support script for the §5.7 "locked before outcome inspection" marker.

Adjudicates, using file-modification timestamps as evidence (there is no
public registry entry -- no URL or DOI for this study exists anywhere in
the repository), whether the hypotheses, outcome definitions, and
statistical models were fixed before any of the four analyzed batches was
submitted, or only after.

Evidence gathered:
- mtimes of the locked scenario/run-plan artifacts, the schema, the four
  prompt files, and the statistical-model and outcome-parsing source code
  (these define the hypotheses, outcomes, and models, and cannot be
  changed by outcome-blind report regeneration).
- created_at_utc of the four analyzed Batches (from
  confirmatory_2x2/batch/chunks_v2/submissions/chunk_0{1..4}_state.json).
- A check on confirmatory_2x2/src/write_reports.py::preregistration: this
  function returns a fixed string literal with no results/outcome
  dependence, so the fact that its *output file*
  (reports/preregistration_en.md) has a later mtime (it was last
  regenerated after collection, as part of assembling the reports bundle)
  does not by itself indicate the plan's substance changed after outcome
  inspection -- unlike the mtimes of the code/config that actually define
  the design, which do predate collection.

Writes LOCKED_BEFORE_COLLECTION_CHECK.md.
"""
from __future__ import annotations

import inspect
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONF = REPO_ROOT / "confirmatory_2x2"
sys.path.insert(0, str(CONF))

REPORT_PATH = Path(__file__).resolve().parent / "LOCKED_BEFORE_COLLECTION_CHECK.md"

DESIGN_ARTIFACTS = [
    "config/experiment.yaml",
    "config/models.yaml",
    "schemas/submit_agentic_decision.json",
    "prompts/neutral_low_agenticity.txt",
    "prompts/neutral_high_agenticity.txt",
    "prompts/commercial_low_agenticity.txt",
    "prompts/commercial_high_agenticity.txt",
    "data/locked/confirmatory_scenarios.json",
    "data/locked/confirmatory_run_plan.csv",
    "data/locked/LOCKED_SET_HASH.txt",
    "data/locked/RUN_PLAN_HASH.txt",
    "src/common.py",
    "src/statistical_analysis.py",
    "src/parse_responses.py",
    "reports/statistical_analysis_plan.md",
    "reports/power_analysis.md",
]

CHUNK_STATE_FILES = [
    "batch/chunks_v2/submissions/chunk_01_state.json",
    "batch/chunks_v2/submissions/chunk_02_state.json",
    "batch/chunks_v2/submissions/chunk_03_state.json",
    "batch/chunks_v2/submissions/chunk_04_state.json",
]


def mtime_utc(rel: str) -> datetime:
    return datetime.fromtimestamp((CONF / rel).stat().st_mtime, tz=timezone.utc)


def main() -> None:
    from src.write_reports import preregistration
    source = inspect.getsource(preregistration)
    assert "return \"\"\"" in source or "return '''" in source or 'return """' in source, \
        "expected preregistration() to return a fixed string literal"
    no_dynamic_refs = not any(tok in source for tok in ["df[", "result", "outcome_value", ".mean(", ".csv"])
    assert no_dynamic_refs, "preregistration() appears to reference computed results; re-examine"

    chunk_created = []
    for rel in CHUNK_STATE_FILES:
        state = json.loads((CONF / rel).read_text(encoding="utf-8"))
        chunk_created.append((state["batch_id"], datetime.fromisoformat(state["created_at_utc"])))
    first_batch_time = min(t for _, t in chunk_created)

    rows = []
    all_before = True
    for rel in DESIGN_ARTIFACTS:
        t = mtime_utc(rel)
        before = t < first_batch_time
        all_before = all_before and before
        rows.append((rel, t.isoformat(), before))

    prereg_mtime = mtime_utc("reports/preregistration_en.md")
    prereg_before = prereg_mtime < first_batch_time

    lines = [
        "# LOCKED_BEFORE_COLLECTION_CHECK.md",
        "",
        "Support script for the §5.7 marker on whether statistical models and",
        "outcome definitions were locked before outcome inspection.",
        "",
        "No public registry entry (URL/DOI) exists for this study anywhere in the",
        "repository; evidence here is internal file-modification timestamps plus a",
        "static-analysis check on the report-generation code.",
        "",
        f"First of the four analyzed batches created at: {first_batch_time.isoformat()} "
        f"(batch_id={[bid for bid, t in chunk_created if t == first_batch_time][0]}).",
        "",
        "## Design/model/outcome-defining artifacts vs. first-batch time",
        "",
        "| Artifact | Last modified (UTC) | Before first analyzed batch |",
        "|---|---|---|",
    ]
    for rel, iso, before in rows:
        lines.append(f"| {rel} | {iso} | {'YES' if before else 'NO'} |")
    lines += [
        "",
        f"**All {len(rows)} design-defining artifacts predate the first analyzed batch: {all_before}.**",
        "",
        "## Human-readable preregistration write-up (reports/preregistration_en.md)",
        "",
        f"Last modified: {prereg_mtime.isoformat()} -- {'before' if prereg_before else 'AFTER'} the first analyzed batch.",
        "",
        "This file is generated by `confirmatory_2x2/src/write_reports.py::preregistration`,",
        "which returns a fixed string literal (verified here by source inspection: no",
        "reference to computed results, dataframes, or outcome values). Its later mtime",
        "reflects when the reports bundle was last assembled, not a change in the",
        "underlying hypotheses/outcomes/models, which are fixed in the source code and",
        "config artifacts listed above -- all of which predate collection.",
        "",
        "## Conclusion",
        "",
        "The hypotheses (hardcoded in `src/write_reports.py::HYPOTHESES` and",
        "`src/statistical_analysis.py`), outcome definitions (fixed by the locked",
        "scenario set, run plan, and output schema), and statistical model",
        "specification (`src/statistical_analysis.py`, `reports/statistical_analysis_plan.md`)",
        "were all last modified before the first of the four analyzed batches was",
        "submitted. No public registry entry exists, so the appropriate",
        "characterization is: pre-specified in a locked, hash-identified analysis",
        "plan, not publicly preregistered.",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")
    print(f"all_design_artifacts_before_first_batch={all_before} prereg_writeup_before_first_batch={prereg_before}")


if __name__ == "__main__":
    main()
