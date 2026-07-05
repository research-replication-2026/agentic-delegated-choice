from __future__ import annotations

import csv
import math
import random

from src.common import load_yaml, logistic, mean, path, write_csv, write_text


def simulate(main_effect: float, interaction: float, seed: int, iterations: int = 350) -> dict:
    rng = random.Random(seed)
    h1_hits = 0
    h2_hits = 0
    for _ in range(iterations):
        scenario_effects = [rng.gauss(0, 0.55) for _ in range(50)]
        domain_effects = {"hotels": rng.gauss(0, 0.08), "software": rng.gauss(0, 0.08), "electronics": rng.gauss(0, 0.08)}
        counts = {"nl": [0, 0], "cl": [0, 0], "nh": [0, 0], "ch": [0, 0]}
        for sid in range(50):
            domain = "hotels" if sid < 20 else "software" if sid < 35 else "electronics"
            for rep in range(10):
                rep_noise = rng.gauss(0, 0.16)
                base_p = logistic(-1.65 + scenario_effects[sid] + domain_effects[domain] + rep_noise)
                for key, commercial, high in [("nl", 0, 0), ("cl", 1, 0), ("nh", 0, 1), ("ch", 1, 1)]:
                    invalid = rng.random() < 0.025
                    if invalid:
                        continue
                    p = min(0.97, max(0.01, base_p + commercial * main_effect + commercial * high * interaction))
                    counts[key][0] += int(rng.random() < p)
                    counts[key][1] += 1
        neutral = counts["nl"][0] + counts["nh"][0]
        neutral_n = counts["nl"][1] + counts["nh"][1]
        commercial = counts["cl"][0] + counts["ch"][0]
        commercial_n = counts["cl"][1] + counts["ch"][1]
        p0 = neutral / neutral_n
        p1 = commercial / commercial_n
        se = math.sqrt(max(1e-9, p0 * (1 - p0) / neutral_n + p1 * (1 - p1) / commercial_n))
        h1_hits += int((p1 - p0) / se > 1.96)
        low_diff = counts["cl"][0] / counts["cl"][1] - counts["nl"][0] / counts["nl"][1]
        high_diff = counts["ch"][0] / counts["ch"][1] - counts["nh"][0] / counts["nh"][1]
        se2 = math.sqrt(sum(max(1e-9, (counts[k][0] / counts[k][1]) * (1 - counts[k][0] / counts[k][1]) / counts[k][1]) for k in counts))
        h2_hits += int(((high_diff - low_diff) / se2) > 1.96)
    return {
        "observations": 2000,
        "commercial_effect_points": main_effect,
        "agenticity_interaction_points": interaction,
        "power_h1_approx": round(h1_hits / iterations, 3),
        "power_h2_approx": round(h2_hits / iterations, 3),
        "iterations": iterations,
    }


def main() -> None:
    cfg = load_yaml("config/experiment.yaml")
    rows = []
    for main_effect in [0.10, 0.15, 0.20, 0.30]:
        for interaction in [0.05, 0.10, 0.15]:
            rows.append(simulate(main_effect, interaction, cfg["random_seeds"]["power"] + len(rows)))
    write_csv("results/tables/power_simulation.csv", rows)
    weak = [r for r in rows if r["agenticity_interaction_points"] == 0.05]
    warning = "The fixed 2,000-observation plan is likely underpowered for an interaction as small as +5 points." if mean([r["power_h2_approx"] for r in weak]) < 0.80 else "The +5 point interaction appears adequately powered under this approximation."
    table = "\n".join(
        f"| {r['commercial_effect_points']} | {r['agenticity_interaction_points']} | {r['power_h1_approx']} | {r['power_h2_approx']} |"
        for r in rows
    )
    write_text("reports/power_analysis.md", f"""
# Power analysis

The simulation fixes the preregistered design at 50 scenarios x 4 conditions x 10 repetitions = 2,000 observations. It includes scenario-level variability, repeated-call correlation, domain differences, invalid responses, a commercial-policy main effect, and a weaker commercial-policy by high-agenticity interaction.

The pilot effect of +50 points is not used for sizing.

| H1 effect | H2 interaction | Approx. H1 power | Approx. H2 power |
| --- | --- | --- | --- |
{table}

{warning}
""")
    print("Power simulation written.")


if __name__ == "__main__":
    main()
