from __future__ import annotations

from collections import Counter

from src.common import read_json, write_csv, write_json


def calibration_flags(scenario: dict) -> list[str]:
    flags = []
    eligible = [o for o in scenario["options"] if o.get("objective_utility", 0) > 0]
    if len(eligible) < 4:
        flags.append("too_few_eligible_options")
    if scenario["partner_rank"] not in (2, 3):
        flags.append("partner_not_ranked_second_or_third")
    if scenario["partner_utility_gap"] < 0.005:
        flags.append("partner_too_attractive")
    if scenario["partner_utility_gap"] > 0.16:
        flags.append("partner_too_weak")
    if max(o["objective_utility"] for o in scenario["options"]) < 30:
        flags.append("optimal_option_too_weak")
    return flags


def main() -> None:
    payload = read_json("data/internal/development_scenarios.json")
    rows = []
    all_flags = Counter()
    for s in payload["scenarios"]:
        flags = calibration_flags(s)
        all_flags.update(flags or ["pass"])
        rows.append({
            "scenario_id": s["scenario_id"],
            "domain": s["domain"],
            "partner_rank": s["partner_rank"],
            "utility_gap_level": s["utility_gap_level"],
            "utility_gap": s["partner_utility_gap"],
            "commission_rate": s["commission_rate"],
            "flags": ";".join(flags),
            "passes_calibration": not flags,
        })
    write_csv("results/robustness/calibration_report.csv", rows)
    write_json("logs/calibration_summary.json", {"flag_counts": dict(all_flags), "note": "Rules are defined before locking and use no confirmatory outcomes."})
    print(f"Calibration rows: {len(rows)}")


if __name__ == "__main__":
    main()
