"""NGO Financial Health Scorecard computation.

Computes KPIs, assigns health ratings (Red/Yellow/Green),
and ranks NGOs by overall financial health score.
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple


# Default thresholds: (green_threshold, yellow_threshold, higher_is_better)
DEFAULT_THRESHOLDS = {
    "program_expense_ratio": {"green": 0.75, "yellow": 0.65, "higher_is_better": True},
    "admin_expense_ratio": {"green": 0.15, "yellow": 0.25, "higher_is_better": False},
    "fundraising_efficiency": {"green": 0.10, "yellow": 0.20, "higher_is_better": False},
    "working_capital_ratio": {"green": 1.5, "yellow": 1.0, "higher_is_better": True},
    "revenue_growth": {"green": 0.05, "yellow": 0.0, "higher_is_better": True},
    "donor_dependency": {"green": 0.50, "yellow": 0.75, "higher_is_better": False},
    "reserves_months": {"green": 6.0, "yellow": 3.0, "higher_is_better": True},
}

DEFAULT_WEIGHTS = {
    "program_expense_ratio": 0.20,
    "admin_expense_ratio": 0.10,
    "fundraising_efficiency": 0.15,
    "working_capital_ratio": 0.15,
    "revenue_growth": 0.10,
    "donor_dependency": 0.15,
    "reserves_months": 0.15,
}


def compute_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """Compute financial KPIs for each NGO-year record.

    Args:
        df: DataFrame with raw financial data.

    Returns:
        DataFrame with computed KPI columns added.
    """
    result = df.copy()

    # Program Expense Ratio = program_expenses / total_expenses
    result["program_expense_ratio"] = (
        result["program_expenses"] / result["total_expenses"]
    ).round(4)

    # Admin Expense Ratio = admin_expenses / total_expenses
    result["admin_expense_ratio"] = (
        result["admin_expenses"] / result["total_expenses"]
    ).round(4)

    # Fundraising Efficiency = fundraising_expenses / total_revenue
    result["fundraising_efficiency"] = (
        result["fundraising_expenses"] / result["total_revenue"]
    ).round(4)

    # Working Capital Ratio = current_assets / current_liabilities
    result["working_capital_ratio"] = (
        result["current_assets"] / result["current_liabilities"]
    ).round(4)

    # Revenue Growth (year-over-year, per NGO)
    result = result.sort_values(["ngo_name", "year"])
    result["revenue_growth"] = result.groupby("ngo_name")["total_revenue"].pct_change()
    result["revenue_growth"] = result["revenue_growth"].round(4)

    # Donor Dependency = donor_revenue / total_revenue
    result["donor_dependency"] = (
        result["donor_revenue"] / result["total_revenue"]
    ).round(4)

    # Reserves in Months = cash_reserves / monthly_operating_expenses
    result["reserves_months"] = (
        result["cash_reserves"] / result["monthly_operating_expenses"]
    ).round(2)

    return result


def assign_rating(
    value: float,
    green_threshold: float,
    yellow_threshold: float,
    higher_is_better: bool = True,
) -> str:
    """Assign a Red/Yellow/Green rating based on thresholds.

    Args:
        value: KPI value.
        green_threshold: Threshold for Green rating.
        yellow_threshold: Threshold for Yellow rating.
        higher_is_better: If True, higher values are better.

    Returns:
        Rating string: 'Green', 'Yellow', or 'Red'.
    """
    if pd.isna(value):
        return "N/A"

    if higher_is_better:
        if value >= green_threshold:
            return "Green"
        elif value >= yellow_threshold:
            return "Yellow"
        else:
            return "Red"
    else:
        if value <= green_threshold:
            return "Green"
        elif value <= yellow_threshold:
            return "Yellow"
        else:
            return "Red"


def rating_to_score(rating: str) -> float:
    """Convert a rating to a numeric score.

    Args:
        rating: 'Green', 'Yellow', 'Red', or 'N/A'.

    Returns:
        Numeric score (3=Green, 2=Yellow, 1=Red, 0=N/A).
    """
    mapping = {"Green": 3.0, "Yellow": 2.0, "Red": 1.0, "N/A": 0.0}
    return mapping.get(rating, 0.0)


def compute_health_scores(
    df: pd.DataFrame,
    thresholds: Optional[Dict[str, Dict]] = None,
    weights: Optional[Dict[str, float]] = None,
) -> pd.DataFrame:
    """Compute health ratings and weighted scores for all KPIs.

    Args:
        df: DataFrame with computed KPIs.
        thresholds: KPI threshold definitions.
        weights: KPI weights for overall score.

    Returns:
        DataFrame with rating and score columns added.
    """
    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS
    if weights is None:
        weights = DEFAULT_WEIGHTS

    result = df.copy()
    kpi_list = list(thresholds.keys())

    # Assign ratings for each KPI
    for kpi in kpi_list:
        t = thresholds[kpi]
        higher = t.get("higher_is_better", True)
        result[f"{kpi}_rating"] = result[kpi].apply(
            lambda v, g=t["green"], y=t["yellow"], h=higher: assign_rating(v, g, y, h)
        )
        result[f"{kpi}_score"] = result[f"{kpi}_rating"].apply(rating_to_score)

    # Compute weighted overall score
    total_weight = sum(weights.get(k, 0) for k in kpi_list)
    result["overall_score"] = 0.0
    for kpi in kpi_list:
        w = weights.get(kpi, 0) / total_weight if total_weight > 0 else 0
        result["overall_score"] += result[f"{kpi}_score"] * w

    result["overall_score"] = result["overall_score"].round(3)

    # Overall rating based on weighted score
    result["overall_rating"] = result["overall_score"].apply(
        lambda s: "Green" if s >= 2.5 else ("Yellow" if s >= 1.75 else "Red")
    )

    return result


def rank_ngos(df: pd.DataFrame, year: Optional[int] = None) -> pd.DataFrame:
    """Rank NGOs by overall health score.

    Args:
        df: DataFrame with health scores computed.
        year: Specific year to rank. If None, uses latest year.

    Returns:
        DataFrame ranked by overall score (descending).
    """
    if year is None:
        year = int(df["year"].max())

    year_df = df[df["year"] == year].copy()
    year_df = year_df.sort_values("overall_score", ascending=False).reset_index(drop=True)
    year_df["rank"] = range(1, len(year_df) + 1)
    return year_df


def get_kpi_summary(df: pd.DataFrame, year: Optional[int] = None) -> pd.DataFrame:
    """Get summary statistics for all KPIs in a given year.

    Args:
        df: DataFrame with computed KPIs.
        year: Year to summarize. Defaults to latest.

    Returns:
        DataFrame with mean, median, min, max for each KPI.
    """
    kpi_cols = [
        "program_expense_ratio", "admin_expense_ratio",
        "fundraising_efficiency", "working_capital_ratio",
        "revenue_growth", "donor_dependency", "reserves_months",
    ]

    if year is None:
        year = int(df["year"].max())

    subset = df[df["year"] == year][kpi_cols]
    summary = subset.describe().loc[["mean", "50%", "min", "max"]].T
    summary = summary.rename(columns={"50%": "median"})
    return summary.round(4)


def get_ngo_trend(df: pd.DataFrame, ngo_name: str) -> pd.DataFrame:
    """Get trend data for a specific NGO across all years.

    Args:
        df: DataFrame with health scores.
        ngo_name: Name of the NGO.

    Returns:
        DataFrame filtered to the specified NGO, sorted by year.
    """
    return df[df["ngo_name"] == ngo_name].sort_values("year").reset_index(drop=True)
