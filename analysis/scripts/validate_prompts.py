from __future__ import annotations

from src.common import read_json, write_json


def main() -> None:
    prompts = read_json("prompts/confirmatory_prompts.json")["prompts"]
    by_scenario: dict[str, list[dict]] = {}
    for p in prompts:
        by_scenario.setdefault(p["scenario_id"], []).append(p)
    issues = []
    for sid, rows in by_scenario.items():
        user_requests = {r["user_payload"]["user_request"] for r in rows}
        option_sets = {tuple(sorted(o["name"] for o in r["user_payload"]["options"])) for r in rows}
        if len(user_requests) != 1:
            issues.append(f"{sid}: user prompt differs")
        if len(option_sets) != 1:
            issues.append(f"{sid}: catalog differs beyond random order")
        for r in rows:
            text = str(r["user_payload"])
            if "partner_option_id" in text or "commission_rate" in text:
                issues.append(f"{sid}: hidden condition leakage")
    write_json("logs/prompt_validation.json", {"valid": not issues, "issues": issues})
    if issues:
        raise SystemExit("; ".join(issues[:5]))
    print("Prompt validation passed.")


if __name__ == "__main__":
    main()
