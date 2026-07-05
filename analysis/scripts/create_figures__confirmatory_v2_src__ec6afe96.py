from __future__ import annotations

import csv

import matplotlib.pyplot as plt

from src.common import path


def main() -> None:
    rows = list(csv.DictReader(path("results/tables/power_simulation.csv").open("r", encoding="utf-8")))
    subset = [r for r in rows if r["assumed_interaction"] == "0.1"]
    plt.figure(figsize=(8, 5))
    for obs in sorted({r["observations"] for r in subset}, key=int):
        xs = [float(r["assumed_main_effect"]) for r in subset if r["observations"] == obs]
        ys = [float(r["power_main_approx"]) for r in subset if r["observations"] == obs]
        plt.plot(xs, ys, marker="o", label=f"{obs} obs")
    plt.axhline(0.8, color="black", linestyle="--", linewidth=1)
    plt.xlabel("Assumed C2 vs C0 main effect")
    plt.ylabel("Approximate power")
    plt.title("Hierarchical power simulation, interaction fixed at +0.10")
    plt.legend()
    plt.tight_layout()
    target = path("results/figures/power_curves.png")
    plt.savefig(target, dpi=180)
    plt.close()
    print(f"Figure written: {target}")


if __name__ == "__main__":
    main()
