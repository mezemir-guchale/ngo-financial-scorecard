"""Visualization module for NGO Financial Health Scorecard."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Optional


def plot_health_bar_chart(
    ranked_df: pd.DataFrame,
    output_path: Optional[str] = None,
    figsize: tuple = (14, 8),
) -> plt.Figure:
    """Create a horizontal bar chart of NGO health scores with color coding.

    Args:
        ranked_df: DataFrame with ranked NGOs (must have overall_score, overall_rating).
        output_path: Path to save figure. If None, figure is not saved.
        figsize: Figure size tuple.

    Returns:
        Matplotlib Figure object.
    """
    color_map = {"Green": "#2ecc71", "Yellow": "#f1c40f", "Red": "#e74c3c"}

    fig, ax = plt.subplots(figsize=figsize)
    colors = [color_map.get(r, "#95a5a6") for r in ranked_df["overall_rating"]]

    bars = ax.barh(
        range(len(ranked_df)),
        ranked_df["overall_score"],
        color=colors,
        edgecolor="white",
        linewidth=0.5,
    )

    ax.set_yticks(range(len(ranked_df)))
    ax.set_yticklabels(ranked_df["ngo_name"], fontsize=9)
    ax.set_xlabel("Overall Health Score", fontsize=12)
    ax.set_title("NGO Financial Health Rankings", fontsize=14, fontweight="bold")
    ax.set_xlim(0, 3.2)
    ax.invert_yaxis()

    # Add score labels
    for i, (score, rating) in enumerate(
        zip(ranked_df["overall_score"], ranked_df["overall_rating"])
    ):
        ax.text(score + 0.05, i, f"{score:.2f} ({rating})", va="center", fontsize=8)

    plt.tight_layout()
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
    return fig


def plot_radar_chart(
    ngo_data: pd.Series,
    kpi_cols: List[str],
    ngo_name: str,
    output_path: Optional[str] = None,
    figsize: tuple = (8, 8),
) -> plt.Figure:
    """Create a radar/spider chart for a single NGO's KPI scores.

    Args:
        ngo_data: Series with KPI score columns.
        kpi_cols: List of KPI column names.
        ngo_name: NGO name for title.
        output_path: Path to save figure.
        figsize: Figure size tuple.

    Returns:
        Matplotlib Figure object.
    """
    score_cols = [f"{k}_score" for k in kpi_cols]
    values = [ngo_data.get(c, 0) for c in score_cols]
    values.append(values[0])  # Close the polygon

    labels = [k.replace("_", " ").title() for k in kpi_cols]
    angles = np.linspace(0, 2 * np.pi, len(kpi_cols), endpoint=False).tolist()
    angles.append(angles[0])

    fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(polar=True))
    ax.plot(angles, values, "o-", linewidth=2, color="#2980b9")
    ax.fill(angles, values, alpha=0.25, color="#2980b9")

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylim(0, 3.5)
    ax.set_yticks([1, 2, 3])
    ax.set_yticklabels(["Red", "Yellow", "Green"], fontsize=8)
    ax.set_title(f"Financial Health Radar: {ngo_name}", fontsize=13, fontweight="bold", pad=20)

    plt.tight_layout()
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
    return fig


def plot_trend_lines(
    trend_df: pd.DataFrame,
    ngo_name: str,
    kpi_cols: List[str],
    output_path: Optional[str] = None,
    figsize: tuple = (14, 10),
) -> plt.Figure:
    """Plot KPI trends over years for a single NGO.

    Args:
        trend_df: DataFrame for a single NGO sorted by year.
        ngo_name: NGO name for title.
        kpi_cols: KPI column names to plot.
        output_path: Path to save figure.
        figsize: Figure size tuple.

    Returns:
        Matplotlib Figure object.
    """
    n_kpis = len(kpi_cols)
    ncols = 2
    nrows = (n_kpis + 1) // 2

    fig, axes = plt.subplots(nrows, ncols, figsize=figsize)
    axes = axes.flatten()

    for i, kpi in enumerate(kpi_cols):
        ax = axes[i]
        years = trend_df["year"].values
        vals = trend_df[kpi].values

        ax.plot(years, vals, "s-", color="#2980b9", linewidth=2, markersize=6)
        ax.set_title(kpi.replace("_", " ").title(), fontsize=11, fontweight="bold")
        ax.set_xlabel("Year", fontsize=9)
        ax.grid(True, alpha=0.3)

        for x, y in zip(years, vals):
            if not np.isnan(y):
                ax.annotate(f"{y:.2f}", (x, y), textcoords="offset points",
                            xytext=(0, 8), fontsize=8, ha="center")

    # Hide unused subplots
    for j in range(n_kpis, len(axes)):
        axes[j].set_visible(False)

    fig.suptitle(f"KPI Trends: {ngo_name}", fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
    return fig


def plot_rating_distribution(
    df: pd.DataFrame,
    year: int,
    output_path: Optional[str] = None,
    figsize: tuple = (12, 6),
) -> plt.Figure:
    """Plot distribution of ratings across KPIs for a given year.

    Args:
        df: DataFrame with rating columns.
        year: Year to visualize.
        output_path: Path to save figure.
        figsize: Figure size.

    Returns:
        Matplotlib Figure object.
    """
    kpi_names = [
        "program_expense_ratio", "admin_expense_ratio",
        "fundraising_efficiency", "working_capital_ratio",
        "revenue_growth", "donor_dependency", "reserves_months",
    ]

    year_df = df[df["year"] == year]
    color_map = {"Green": "#2ecc71", "Yellow": "#f1c40f", "Red": "#e74c3c", "N/A": "#bdc3c7"}

    fig, ax = plt.subplots(figsize=figsize)
    x = np.arange(len(kpi_names))
    bar_width = 0.25

    for i, rating in enumerate(["Green", "Yellow", "Red"]):
        counts = []
        for kpi in kpi_names:
            col = f"{kpi}_rating"
            if col in year_df.columns:
                counts.append((year_df[col] == rating).sum())
            else:
                counts.append(0)
        ax.bar(x + i * bar_width, counts, bar_width,
               label=rating, color=color_map[rating], edgecolor="white")

    ax.set_xticks(x + bar_width)
    ax.set_xticklabels([k.replace("_", " ").title() for k in kpi_names],
                       rotation=30, ha="right", fontsize=9)
    ax.set_ylabel("Number of NGOs", fontsize=11)
    ax.set_title(f"Rating Distribution by KPI ({year})", fontsize=13, fontweight="bold")
    ax.legend(fontsize=10)

    plt.tight_layout()
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
    return fig
