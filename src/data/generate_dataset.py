"""Generate synthetic NGO financial data for analysis."""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

from src.utils.config import get_project_root


NGO_NAMES = [
    "Hope Foundation", "Global Aid Network", "Children First Trust",
    "Green Earth Alliance", "Health for All Initiative", "Education Bridge",
    "Water of Life", "Shelter Now International", "Feed the Future",
    "Women Empowerment League", "Tech for Good", "Rural Development Corp",
    "Peace Builders Forum", "Clean Energy Foundation", "Youth Uplift",
    "Community Health Partners", "Disaster Relief Network", "Arts for Change",
    "Animal Welfare Trust", "Refugee Support Alliance",
]

NGO_SECTORS = [
    "Human Services", "International Aid", "Child Welfare",
    "Environment", "Healthcare", "Education",
    "Water & Sanitation", "Housing", "Food Security",
    "Women's Rights", "Technology", "Rural Development",
    "Peacebuilding", "Energy", "Youth Development",
    "Healthcare", "Emergency Relief", "Arts & Culture",
    "Animal Welfare", "Refugee Services",
]


def generate_ngo_financial_data(
    num_ngos: int = 20,
    num_years: int = 5,
    start_year: int = 2021,
    seed: int = 42,
) -> pd.DataFrame:
    """Generate synthetic NGO financial data.

    Creates realistic financial data for multiple NGOs across several years,
    including revenue breakdown, expenses, assets, and liabilities.

    Args:
        num_ngos: Number of NGOs to generate.
        num_years: Number of years of data.
        start_year: First year of data.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with NGO financial data.
    """
    rng = np.random.RandomState(seed)
    records = []

    for i in range(min(num_ngos, len(NGO_NAMES))):
        name = NGO_NAMES[i]
        sector = NGO_SECTORS[i]

        # Base financial profile for this NGO
        base_revenue = rng.uniform(500_000, 50_000_000)
        growth_rate = rng.uniform(-0.02, 0.10)
        donor_share = rng.uniform(0.30, 0.90)
        program_ratio = rng.uniform(0.55, 0.90)
        admin_ratio = rng.uniform(0.05, 0.25)

        for y in range(num_years):
            year = start_year + y
            year_factor = (1 + growth_rate) ** y
            noise = rng.uniform(0.90, 1.10)

            total_revenue = base_revenue * year_factor * noise

            # Revenue breakdown
            donor_revenue = total_revenue * donor_share * rng.uniform(0.90, 1.10)
            grant_revenue = total_revenue * rng.uniform(0.05, 0.30)
            earned_revenue = max(0, total_revenue - donor_revenue - grant_revenue)

            actual_total_revenue = donor_revenue + grant_revenue + earned_revenue

            # Expenses
            prog_expense = actual_total_revenue * program_ratio * rng.uniform(0.92, 1.08)
            admin_expense = actual_total_revenue * admin_ratio * rng.uniform(0.90, 1.10)
            fundraising_expense = actual_total_revenue * rng.uniform(0.03, 0.15)
            total_expenses = prog_expense + admin_expense + fundraising_expense

            # Balance sheet items
            current_assets = actual_total_revenue * rng.uniform(0.20, 0.80)
            current_liabilities = current_assets * rng.uniform(0.20, 0.90)
            total_assets = current_assets + actual_total_revenue * rng.uniform(0.10, 0.50)
            net_assets = total_assets - current_liabilities - actual_total_revenue * rng.uniform(0.0, 0.15)
            cash_reserves = current_assets * rng.uniform(0.30, 0.80)

            # Monthly operating expenses (for reserves calculation)
            monthly_operating = total_expenses / 12.0

            records.append({
                "ngo_name": name,
                "sector": sector,
                "year": year,
                "total_revenue": round(actual_total_revenue, 2),
                "donor_revenue": round(donor_revenue, 2),
                "grant_revenue": round(grant_revenue, 2),
                "earned_revenue": round(earned_revenue, 2),
                "program_expenses": round(prog_expense, 2),
                "admin_expenses": round(admin_expense, 2),
                "fundraising_expenses": round(fundraising_expense, 2),
                "total_expenses": round(total_expenses, 2),
                "current_assets": round(current_assets, 2),
                "current_liabilities": round(current_liabilities, 2),
                "total_assets": round(total_assets, 2),
                "net_assets": round(net_assets, 2),
                "cash_reserves": round(cash_reserves, 2),
                "monthly_operating_expenses": round(monthly_operating, 2),
            })

    df = pd.DataFrame(records)
    return df


def save_dataset(
    df: pd.DataFrame,
    output_dir: Optional[str] = None,
    filename: str = "ngo_financial_data.csv",
) -> Path:
    """Save generated dataset to CSV.

    Args:
        df: DataFrame to save.
        output_dir: Output directory. Defaults to data/raw.
        filename: Output filename.

    Returns:
        Path to saved file.
    """
    if output_dir is None:
        output_dir = get_project_root() / "data" / "raw"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    df.to_csv(output_path, index=False)
    return output_path


if __name__ == "__main__":
    df = generate_ngo_financial_data()
    path = save_dataset(df)
    print(f"Generated {len(df)} records, saved to {path}")
    print(df.head())
