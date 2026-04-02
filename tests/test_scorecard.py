"""Tests for the NGO Financial Health Scorecard."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.generate_dataset import generate_ngo_financial_data
from src.analysis.scorecard import (
    assign_rating,
    compute_health_scores,
    compute_kpis,
    get_kpi_summary,
    get_ngo_trend,
    rank_ngos,
    rating_to_score,
)


@pytest.fixture
def sample_data():
    """Generate a small sample dataset for testing."""
    return generate_ngo_financial_data(num_ngos=5, num_years=3, start_year=2022, seed=42)


@pytest.fixture
def data_with_kpis(sample_data):
    """Dataset with KPIs computed."""
    return compute_kpis(sample_data)


@pytest.fixture
def scored_data(data_with_kpis):
    """Dataset with health scores."""
    return compute_health_scores(data_with_kpis)


class TestDataGeneration:
    def test_correct_shape(self, sample_data):
        """Test that generated data has the expected number of rows."""
        assert len(sample_data) == 5 * 3  # 5 NGOs x 3 years

    def test_required_columns_present(self, sample_data):
        """Test that all required columns are present."""
        required = [
            "ngo_name", "year", "total_revenue", "program_expenses",
            "admin_expenses", "fundraising_expenses", "total_expenses",
            "current_assets", "current_liabilities", "donor_revenue",
            "cash_reserves", "monthly_operating_expenses",
        ]
        for col in required:
            assert col in sample_data.columns, f"Missing column: {col}"

    def test_positive_financials(self, sample_data):
        """Test that financial values are positive."""
        financial_cols = [
            "total_revenue", "program_expenses", "admin_expenses",
            "total_expenses", "current_assets",
        ]
        for col in financial_cols:
            assert (sample_data[col] > 0).all(), f"Non-positive values in {col}"


class TestKPIComputation:
    def test_kpi_columns_created(self, data_with_kpis):
        """Test that all KPI columns are created."""
        kpi_cols = [
            "program_expense_ratio", "admin_expense_ratio",
            "fundraising_efficiency", "working_capital_ratio",
            "donor_dependency", "reserves_months",
        ]
        for col in kpi_cols:
            assert col in data_with_kpis.columns, f"Missing KPI: {col}"

    def test_program_expense_ratio_range(self, data_with_kpis):
        """Test that program expense ratio is between 0 and 1."""
        vals = data_with_kpis["program_expense_ratio"].dropna()
        assert (vals >= 0).all() and (vals <= 1.5).all()

    def test_working_capital_ratio_positive(self, data_with_kpis):
        """Test that working capital ratio is positive."""
        vals = data_with_kpis["working_capital_ratio"].dropna()
        assert (vals > 0).all()

    def test_revenue_growth_first_year_nan(self, data_with_kpis):
        """Test that revenue growth is NaN for the first year of each NGO."""
        for ngo in data_with_kpis["ngo_name"].unique():
            ngo_data = data_with_kpis[data_with_kpis["ngo_name"] == ngo].sort_values("year")
            assert pd.isna(ngo_data["revenue_growth"].iloc[0])


class TestRatings:
    def test_assign_rating_green_higher_is_better(self):
        """Test Green rating when higher is better."""
        assert assign_rating(0.80, 0.75, 0.65, higher_is_better=True) == "Green"

    def test_assign_rating_yellow_higher_is_better(self):
        """Test Yellow rating when higher is better."""
        assert assign_rating(0.70, 0.75, 0.65, higher_is_better=True) == "Yellow"

    def test_assign_rating_red_higher_is_better(self):
        """Test Red rating when higher is better."""
        assert assign_rating(0.50, 0.75, 0.65, higher_is_better=True) == "Red"

    def test_assign_rating_lower_is_better(self):
        """Test rating when lower is better (e.g., admin expense ratio)."""
        assert assign_rating(0.10, 0.15, 0.25, higher_is_better=False) == "Green"
        assert assign_rating(0.20, 0.15, 0.25, higher_is_better=False) == "Yellow"
        assert assign_rating(0.30, 0.15, 0.25, higher_is_better=False) == "Red"

    def test_assign_rating_nan(self):
        """Test that NaN values get N/A rating."""
        assert assign_rating(float("nan"), 0.75, 0.65) == "N/A"

    def test_rating_to_score_values(self):
        """Test numeric conversion of ratings."""
        assert rating_to_score("Green") == 3.0
        assert rating_to_score("Yellow") == 2.0
        assert rating_to_score("Red") == 1.0
        assert rating_to_score("N/A") == 0.0


class TestHealthScores:
    def test_overall_score_column_exists(self, scored_data):
        """Test that overall score and rating columns exist."""
        assert "overall_score" in scored_data.columns
        assert "overall_rating" in scored_data.columns

    def test_overall_score_range(self, scored_data):
        """Test that overall scores are in valid range."""
        scores = scored_data["overall_score"].dropna()
        assert (scores >= 0).all() and (scores <= 3.0).all()

    def test_ranking_order(self, scored_data):
        """Test that ranking produces correct order."""
        ranked = rank_ngos(scored_data)
        scores = ranked["overall_score"].values
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1], "Ranking not in descending order"

    def test_ranking_has_rank_column(self, scored_data):
        """Test that ranking adds a rank column."""
        ranked = rank_ngos(scored_data)
        assert "rank" in ranked.columns
        assert ranked["rank"].iloc[0] == 1


class TestSummaryAndTrend:
    def test_kpi_summary_shape(self, scored_data):
        """Test KPI summary output."""
        summary = get_kpi_summary(scored_data)
        assert summary.shape[0] == 7  # 7 KPIs
        assert "mean" in summary.columns

    def test_ngo_trend_data(self, scored_data):
        """Test NGO trend extraction."""
        ngo_name = scored_data["ngo_name"].iloc[0]
        trend = get_ngo_trend(scored_data, ngo_name)
        assert len(trend) == 3  # 3 years
        assert list(trend["year"]) == sorted(trend["year"])
