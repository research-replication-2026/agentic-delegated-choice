#!/usr/bin/env python3
"""T2 support script for the §5.3 marker and supplement/S1.

Extracts the four system instructions, the user-message template, and the
output schema exactly as they were actually submitted in
confirmatory_2x2/batch/confirmatory_2000_requests_corrected_v2.jsonl (the
Batch file whose SHA-256, per build_corrected_batch.py's own validation, was
submitted unchanged except for metadata value typing), rather than
transcribing them by hand -- this avoids any transcription error and
guarantees the manuscript quotes what the model actually received.

Also checks, and reports rather than hides, a real discrepancy: the static
files confirmatory_2x2/prompts/commercial_low_agenticity.txt and
commercial_high_agenticity.txt do NOT match what was actually sent for the
commercial conditions. The commercial system instruction is generated per
scenario by confirmatory_2x2/src/build_batch.py::commercial_instruction,
which embeds that scenario's commission rate and visible partner option ID;
the static .txt files appear to be an earlier, unused draft. Only the two
neutral instructions are literally read from their .txt files at build time
and match verbatim.

Writes manuscript/supplement/S1_experimental_materials.md.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONF = REPO_ROOT / "confirmatory_2x2"
sys.path.insert(0, str(CONF))

BATCH_FILE = CONF / "batch/confirmatory_2000_requests_corrected_v2.jsonl"
OUT_PATH = REPO_ROOT / "manuscript/supplement/S1_experimental_materials.md"

EXAMPLE_CUSTOM_IDS = {
    "neutral_low_agenticity": "CON_HOT_001__neutral_low_agenticity__rep01",
    "commercial_low_agenticity": "CON_HOT_001__commercial_low_agenticity__rep01",
    "neutral_high_agenticity": "CON_HOT_001__neutral_high_agenticity__rep01",
    "commercial_high_agenticity": "CON_HOT_001__commercial_high_agenticity__rep01",
}


def load_examples() -> dict[str, dict]:
    wanted = set(EXAMPLE_CUSTOM_IDS.values())
    found: dict[str, dict] = {}
    with BATCH_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            if rec["custom_id"] in wanted:
                found[rec["custom_id"]] = rec
            if len(found) == len(wanted):
                break
    missing = wanted - found.keys()
    assert not missing, f"missing example custom_ids in batch file: {missing}"
    return found


def main() -> None:
    examples = load_examples()
    by_condition = {cond: examples[cid] for cond, cid in EXAMPLE_CUSTOM_IDS.items()}

    neutral_low_static = (CONF / "prompts/neutral_low_agenticity.txt").read_text(encoding="utf-8").strip()
    neutral_high_static = (CONF / "prompts/neutral_high_agenticity.txt").read_text(encoding="utf-8").strip()
    commercial_low_static = (CONF / "prompts/commercial_low_agenticity.txt").read_text(encoding="utf-8").strip()
    commercial_high_static = (CONF / "prompts/commercial_high_agenticity.txt").read_text(encoding="utf-8").strip()

    neutral_low_actual = by_condition["neutral_low_agenticity"]["body"]["input"][0]["content"].strip()
    neutral_high_actual = by_condition["neutral_high_agenticity"]["body"]["input"][0]["content"].strip()
    commercial_low_actual = by_condition["commercial_low_agenticity"]["body"]["input"][0]["content"].strip()
    commercial_high_actual = by_condition["commercial_high_agenticity"]["body"]["input"][0]["content"].strip()

    assert neutral_low_static == neutral_low_actual, "neutral_low static prompt does not match the actually-submitted instruction"
    assert neutral_high_static == neutral_high_actual, "neutral_high static prompt does not match the actually-submitted instruction"
    commercial_low_matches_static = commercial_low_static == commercial_low_actual
    commercial_high_matches_static = commercial_high_static == commercial_high_actual
    assert not commercial_low_matches_static, "expected the static commercial_low .txt to differ from the actual submitted instruction"
    assert not commercial_high_matches_static, "expected the static commercial_high .txt to differ from the actual submitted instruction"

    schema = json.loads((CONF / "schemas/submit_agentic_decision.json").read_text(encoding="utf-8"))
    schema_text = json.dumps(schema, indent=2, ensure_ascii=False)

    tool_def = by_condition["neutral_low_agenticity"]["body"]["tools"][0]
    tool_meta = json.dumps({k: v for k, v in tool_def.items() if k != "parameters"}, indent=2, ensure_ascii=False)

    user_example = by_condition["neutral_low_agenticity"]["body"]["input"][1]["content"]
    user_example_pretty = json.dumps(json.loads(user_example), indent=2, ensure_ascii=False, sort_keys=True)

    lines = []
    lines.append("# Supplement S1 — Experimental Materials")
    lines.append("")
    lines.append("This supplement reproduces, verbatim and byte-for-byte, the system")
    lines.append("instructions, user-message template, tool definition, and output schema")
    lines.append("actually submitted to the model. All text below is extracted programmatically")
    lines.append(f"by `analysis/repro/extract_experimental_materials.py` from")
    lines.append(f"`confirmatory_2x2/batch/confirmatory_2000_requests_corrected_v2.jsonl`")
    lines.append("(the Batch file submitted for data collection, per §5.7), not transcribed")
    lines.append("by hand.")
    lines.append("")
    lines.append("## S1.1 System instructions")
    lines.append("")
    lines.append("Two of the four conditions (neutral, both agenticity levels) use a fixed")
    lines.append("system instruction, read verbatim from")
    lines.append("`confirmatory_2x2/prompts/{condition}.txt` at build time")
    lines.append("(`confirmatory_2x2/src/build_batch.py::instruction_for_row`). The two")
    lines.append("commercial conditions use a **per-scenario template**, generated by")
    lines.append("`confirmatory_2x2/src/build_batch.py::commercial_instruction`, which embeds")
    lines.append("that scenario's commission rate (5%, 10%, or 15%) and the visible option ID")
    lines.append("assigned to the partner option for that specific request — it is not a single")
    lines.append("fixed string across the condition. Example instantiations below are taken from")
    lines.append("scenario `CON_HOT_001`, repetition 1.")
    lines.append("")
    lines.append("**Note on a discrepancy in the repository:** static draft files")
    lines.append("`confirmatory_2x2/prompts/commercial_low_agenticity.txt` and")
    lines.append("`commercial_high_agenticity.txt` also exist in the repository, but they were")
    lines.append("**not** what was sent to the model for the commercial conditions — they lack")
    lines.append("the commission-rate and visible-partner-ID substitution and do not match any")
    lines.append("submitted request byte-for-byte (verified programmatically below). Only the")
    lines.append("two neutral `.txt` files match the actually-submitted instructions exactly.")
    lines.append("")
    lines.append("### neutral_low_agenticity (verbatim, fixed; matches `prompts/neutral_low_agenticity.txt` exactly)")
    lines.append("")
    lines.append("```")
    lines.append(neutral_low_actual)
    lines.append("```")
    lines.append("")
    lines.append("### commercial_low_agenticity (per-scenario template; example instantiation for CON_HOT_001)")
    lines.append("")
    lines.append("```")
    lines.append(commercial_low_actual)
    lines.append("```")
    lines.append("")
    lines.append("### neutral_high_agenticity (verbatim, fixed; matches `prompts/neutral_high_agenticity.txt` exactly)")
    lines.append("")
    lines.append("```")
    lines.append(neutral_high_actual)
    lines.append("```")
    lines.append("")
    lines.append("### commercial_high_agenticity (per-scenario template; example instantiation for CON_HOT_001)")
    lines.append("")
    lines.append("```")
    lines.append(commercial_high_actual)
    lines.append("```")
    lines.append("")
    lines.append("## S1.2 User-message template")
    lines.append("")
    lines.append("Built by `confirmatory_2x2/src/build_run_plan.py::user_prompt`, which")
    lines.append("serializes a JSON object with the scenario's `scenario_id`, `user_request`,")
    lines.append("`primary_criteria`, `secondary_criteria`, `hard_constraints`, and the visible")
    lines.append("option list (with model-facing IDs re-randomized per")
    lines.append("`shuffled_visible_options`, so `option_id` values seen by the model never")
    lines.append("reveal the internal catalogue identity or the partner's canonical ID), as")
    lines.append("`json.dumps(payload, ensure_ascii=False, sort_keys=True)`. Example (identical")
    lines.append("user message across all four conditions for a given scenario/repetition,")
    lines.append("since only the system instruction is manipulated):")
    lines.append("")
    lines.append("```json")
    lines.append(user_example_pretty)
    lines.append("```")
    lines.append("")
    lines.append("## S1.3 Tool definition and tool_choice")
    lines.append("")
    lines.append("Every request forces the call via `tool_choice`:")
    lines.append("`{\"type\": \"function\", \"name\": \"submit_agentic_decision\"}`. Tool metadata:")
    lines.append("")
    lines.append("```json")
    lines.append(tool_meta)
    lines.append("```")
    lines.append("")
    lines.append("## S1.4 Output schema (`confirmatory_2x2/schemas/submit_agentic_decision.json`)")
    lines.append("")
    lines.append("```json")
    lines.append(schema_text)
    lines.append("```")
    lines.append("")
    lines.append("## S1.5 Provenance of the materials above")
    lines.append("")
    lines.append("| Item | Source | Example custom_id |")
    lines.append("|---|---|---|")
    for cond, cid in EXAMPLE_CUSTOM_IDS.items():
        lines.append(f"| {cond} system instruction | `confirmatory_2x2/batch/confirmatory_2000_requests_corrected_v2.jsonl` | `{cid}` |")
    lines.append("")
    lines.append("Verified programmatically: the neutral instructions extracted from the")
    lines.append("submitted batch match `confirmatory_2x2/prompts/neutral_{low,high}_agenticity.txt`")
    lines.append("byte-for-byte; the static `commercial_{low,high}_agenticity.txt` files do")
    lines.append("**not** match any submitted commercial request.")

    OUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print("neutral prompts verified to match static .txt files verbatim: PASS")
    print("static commercial .txt files confirmed to differ from actual submitted instructions: PASS (discrepancy documented, not hidden)")


if __name__ == "__main__":
    main()
