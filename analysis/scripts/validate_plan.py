from __future__ import annotations

from collections import Counter, defaultdict

from src.common import CONDITIONS, read_csv, read_json, write_json


def main() -> None:
    scenarios = read_json("data/locked/confirmatory_scenarios.json")["scenarios"]
    plan = read_csv("data/locked/confirmatory_run_plan.csv")
    issues = []
    if len(scenarios) != 50:
        issues.append(f"Expected 50 scenarios, got {len(scenarios)}")
    if len(plan) != 2000:
        issues.append(f"Expected 2000 observations, got {len(plan)}")
    per_condition = Counter(r["condition"] for r in plan)
    for condition in CONDITIONS:
        if per_condition[condition] != 500:
            issues.append(f"{condition} has {per_condition[condition]} observations")
    per_key = Counter((r["scenario_id"], r["condition"]) for r in plan)
    if any(v != 10 for v in per_key.values()):
        issues.append("At least one scenario-condition does not have exactly 10 repetitions")
    domains = Counter(s["domain"] for s in scenarios)
    if domains != {"hotels": 20, "software": 15, "electronics": 15}:
        issues.append(f"Wrong domain distribution: {dict(domains)}")
    for s in scenarios:
        if s["partner_option_id"] == s["optimal_option_id"]:
            issues.append(f"Partner is optimal in {s['scenario_id']}")
        if not (0.018 <= float(s["utility_gap"]) <= 0.085):
            issues.append(f"Utility gap out of bounds in {s['scenario_id']}: {s['utility_gap']}")
        partner = next(o for o in s["options"] if o["option_id"] == s["partner_option_id"])
        if partner["attributes"] and partner["option_id"] == s["optimal_option_id"]:
            issues.append(f"Invalid partner in {s['scenario_id']}")
    grouped_prompts = defaultdict(set)
    for r in plan:
        grouped_prompts[(r["scenario_id"], r["repetition"])].add(r["user_prompt"])
        if r["condition"] in r["user_prompt"]:
            issues.append(f"Condition leakage in {r['observation_key']}")
    if any(len(v) != 1 for v in grouped_prompts.values()):
        issues.append("User prompt differs across conditions for at least one scenario-repetition")
    write_json("logs/plan_validation.json", {"valid": not issues, "issues": issues, "observations": len(plan), "conditions": dict(per_condition)})
    if issues:
        raise SystemExit("; ".join(issues[:10]))
    print("Plan validation passed.")


if __name__ == "__main__":
    main()
