from __future__ import annotations

import pandas as pd
import matplotlib.pyplot as plt
from pandas.errors import EmptyDataError

from src.analyze_pilot import descriptive_tables
from src.settings import path


FIGURES = [
    ("partner_selection_rate", "Partner selection rate by experimental condition", "Partner selection rate", "figure_1_partner_selection_rate"),
    ("optimal_selection_rate", "Optimal option selection rate by experimental condition", "Optimal option selection rate", "figure_2_optimal_selection_rate"),
    ("mean_regret", "Mean normalized utility regret by experimental condition", "Mean normalized regret", "figure_3_mean_normalized_regret"),
    ("mean_alternatives_presented", "Number of alternatives presented by experimental condition", "Mean alternatives presented", "figure_4_alternatives_presented"),
    ("commercial_disclosure_rate", "Commercial disclosure rate by experimental condition", "Disclosure rate", "figure_5_commercial_disclosure_rate"),
]


def create_figures() -> None:
    df_path = path("data/processed/pilot_results.csv")
    try:
        df = pd.read_csv(df_path) if df_path.exists() and df_path.stat().st_size > 1 else pd.DataFrame()
    except EmptyDataError:
        df = pd.DataFrame()
    table, _ = descriptive_tables(df)
    fig_dir = path("results/pilot/figures")
    fig_dir.mkdir(parents=True, exist_ok=True)
    for metric, title, ylabel, filename in FIGURES:
        fig, ax = plt.subplots(figsize=(9, 5))
        if table.empty:
            ax.text(0.5, 0.5, "No pilot observations available", ha="center", va="center")
            ax.set_xticks([])
        else:
            ax.bar(table["condition"], table[metric], color=["#4C78A8", "#F58518", "#54A24B", "#E45756"])
            ax.tick_params(axis="x", rotation=25)
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.set_xlabel("Experimental condition")
        fig.tight_layout()
        fig.savefig(fig_dir / f"{filename}.png", dpi=300)
        fig.savefig(fig_dir / f"{filename}.pdf")
        plt.close(fig)


if __name__ == "__main__":
    create_figures()
    print("Figures created")
