"""Data loading utilities for NGO financial data."""

import pandas as pd
from pathlib import Path
from typing import Optional

from src.utils.config import get_project_root


def load_ngo_data(
    filepath: Optional[str] = None,
    filename: str = "ngo_financial_data.csv",
) -> pd.DataFrame:
    """Load NGO financial data from CSV.

    Args:
        filepath: Full path to CSV file. If None, looks in data/raw/.
        filename: Filename to load if filepath is None.

    Returns:
        DataFrame with NGO financial data.

    Raises:
        FileNotFoundError: If the data file does not exist.
    """
    if filepath is None:
        filepath = get_project_root() / "data" / "raw" / filename
    else:
        filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"Data file not found: {filepath}")

    df = pd.read_csv(filepath)

    expected_cols = [
        "ngo_name", "year", "total_revenue", "program_expenses",
        "admin_expenses", "fundraising_expenses", "total_expenses",
    ]
    missing = [c for c in expected_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    return df


def filter_by_year(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Filter data for a specific year."""
    return df[df["year"] == year].copy()


def filter_by_ngo(df: pd.DataFrame, ngo_name: str) -> pd.DataFrame:
    """Filter data for a specific NGO."""
    return df[df["ngo_name"] == ngo_name].copy()


def get_latest_year(df: pd.DataFrame) -> int:
    """Get the most recent year in the dataset."""
    return int(df["year"].max())
