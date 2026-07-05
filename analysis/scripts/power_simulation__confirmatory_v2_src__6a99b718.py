from __future__ import annotations

import math
import random

from src.common import load_yaml, logistic, write_csv


def simulate_plan(scenarios: int, reps: int, main_effect: float, interaction: float, seed: int, iterations: int = 300) -> dict:
    rng = random.Random(seed)
    detections_main = 0
    detections_interaction = 0
    for _ in range(iterations):
        scenario_effects = [rng.gauss(0, 0.45) for _ in range(scenarios)]
        c0 = c2 = c2_high = c2_low = 0
        n0 = n2 = n2_high = n2_low = 0
        for s_eff in scenario_effects:
            for agenticity in (0, 1):
                for rep in range(reps):
                    base = -1.5 + s_eff + rng.gauss(0, 0.2)
                    p0 = logistic(base)
                    p2 = min(max(p0 + main_effect + interaction * agenticity, 0.01), 0.99)
                    c0 += rng.random() < p0
                    n0 += 1
                    c2 += rng.random() < p2
                    n2 += 1
                    if agenticity:
                        c2_high += rng.random() < p2
                        n2_high += 1
                    else:
                        c2_low += rng.random() < p2
                        n2_low += 1
        diff = c2 / n2 - c0 / n0
        se = math.sqrt(max(1e-6, (c2 / n2) * (1 - c2 / n2) / n2 + (c0 / n0) * (1 - c0 / n0) / n0))
        if diff / se > 1.96:
            detections_main += 1
        idiff = c2_high / n2_high - c2_low / n2_low
        ise = math.sqrt(max(1e-6, (c2_high / n2_high) * (1 - c2_high / n2_high) / n2_high + (c2_low / n2_low) * (1 - c2_low / n2_low) / n2_low))
        if idiff / ise > 1.96:
            detections_interaction += 1
    return {
        "scenarios": scenarios,
        "repetitions": reps,
        "observations": scenarios * 6 * reps,
        "assumed_main_effect": main_effect,
        "assumed_interaction": interaction,
        "power_main_approx": round(detections_main / iterations, 3),
        "power_interaction_approx": round(detections_interaction / iterations, 3),
        "iterations": iterations,
    }


def main() -> None:
    cfg = load_yaml("config/experiment.yaml")
    rows = []
    plan_specs = [(40, 5), (60, 8), (60, 10), (80, 8)]
    for scenarios, reps in plan_specs:
        for main_effect in [0.10, 0.15, 0.20, 0.30]:
            for interaction in [0.05, 0.075, 0.10, 0.15]:
                rows.append(simulate_plan(scenarios, reps, main_effect, interaction, cfg["random_seeds"]["power"] + len(rows)))
    write_csv("results/tables/power_simulation.csv", rows)
    print(f"Power rows: {len(rows)}")


if __name__ == "__main__":
    main()
