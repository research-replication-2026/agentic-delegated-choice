from __future__ import annotations

import base64
import csv

from src.common import path
from src.provenance import require_real_batch_data

PNG_1X1 = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII=")


def fallback_png(rel: str) -> None:
    target = path(rel)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(PNG_1X1)


def main() -> None:
    require_real_batch_data()
    rows = list(csv.DictReader(path("results/tables/power_simulation.csv").open("r", encoding="utf-8")))
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        fallback_png("results/figures/power_curve_h1.png")
        fallback_png("results/figures/power_curve_h2.png")
        print("Matplotlib unavailable; placeholder PNGs written.")
        return
    for outcome, ycol, filename in [
        ("H1", "power_h1_approx", "results/figures/power_curve_h1.png"),
        ("H2", "power_h2_approx", "results/figures/power_curve_h2.png"),
    ]:
        plt.figure(figsize=(7, 4.5))
        interactions = sorted({float(r["agenticity_interaction_points"]) for r in rows})
        for interaction in interactions:
            subset = [r for r in rows if float(r["agenticity_interaction_points"]) == interaction]
            xs = [float(r["commercial_effect_points"]) for r in subset]
            ys = [float(r[ycol]) for r in subset]
            plt.plot(xs, ys, marker="o", label=f"interaction {interaction:.2f}")
        plt.axhline(0.8, color="black", linestyle="--", linewidth=1)
        plt.ylim(0, 1.05)
        plt.xlabel("Commercial main effect")
        plt.ylabel("Approximate power")
        plt.title(f"Power curve {outcome}, 2,000 observations")
        plt.legend()
        plt.tight_layout()
        plt.savefig(path(filename), dpi=180)
        plt.close()
    print("Figures written.")


if __name__ == "__main__":
    main()
