"""Main pipeline script for NGO Financial Health Scorecard."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import matplotlib
matplotlib.use("Agg")

from src.utils.config import load_config, ensure_directories
from src.utils.logger import setup_logger
from src.data.generate_dataset import generate_ngo_financial_data, save_dataset
from src.data.loader import load_ngo_data
from src.analysis.scorecard import (
    compute_kpis, compute_health_scores, rank_ngos,
    get_kpi_summary, get_ngo_trend,
)
from src.visualization.charts import (
    plot_health_bar_chart, plot_radar_chart,
    plot_trend_lines, plot_rating_distribution,
)


def main():
    """Run the full NGO Financial Health Scorecard pipeline."""
    config = load_config()
    ensure_directories(config)
    logger = setup_logger("ngo_scorecard", config, "pipeline.log")

    logger.info("=" * 60)
    logger.info("NGO Financial Health Scorecard Pipeline")
    logger.info("=" * 60)

    # Step 1: Generate data
    logger.info("Step 1: Generating synthetic NGO financial data...")
    df = generate_ngo_financial_data(
        num_ngos=config["data"]["num_ngos"],
        num_years=config["data"]["num_years"],
        start_year=config["data"]["start_year"],
    )
    raw_path = save_dataset(df, str(project_root / config["data"]["raw_dir"]))
    logger.info(f"Generated {len(df)} records, saved to {raw_path}")

    # Step 2: Load and compute KPIs
    logger.info("Step 2: Computing financial KPIs...")
    df = load_ngo_data(str(raw_path))
    df = compute_kpis(df)
    logger.info(f"Computed KPIs for {df['ngo_name'].nunique()} NGOs across {df['year'].nunique()} years")

    # Step 3: Compute health scores
    logger.info("Step 3: Computing health scores and ratings...")
    df = compute_health_scores(df)

    # Save processed data
    processed_dir = project_root / config["data"]["processed_dir"]
    processed_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(processed_dir / "ngo_scorecard_results.csv", index=False)
    logger.info(f"Saved processed data to {processed_dir}")

    # Step 4: Rank NGOs
    logger.info("Step 4: Ranking NGOs...")
    latest_year = int(df["year"].max())
    ranked = rank_ngos(df, latest_year)

    logger.info(f"\nTop 5 NGOs ({latest_year}):")
    for _, row in ranked.head(5).iterrows():
        logger.info(
            f"  #{int(row['rank'])} {row['ngo_name']}: "
            f"{row['overall_score']:.3f} ({row['overall_rating']})"
        )

    # Step 5: Generate KPI summary
    logger.info("Step 5: KPI Summary Statistics...")
    summary = get_kpi_summary(df, latest_year)
    logger.info(f"\n{summary.to_string()}")

    # Step 6: Generate visualizations
    logger.info("Step 6: Generating visualizations...")
    fig_dir = project_root / config["visualization"]["output_dir"]
    fig_dir.mkdir(parents=True, exist_ok=True)

    # Health bar chart
    fig = plot_health_bar_chart(ranked, str(fig_dir / "health_rankings.png"))
    plt_close(fig)
    logger.info("  Created health_rankings.png")

    # Rating distribution
    fig = plot_rating_distribution(df, latest_year, str(fig_dir / "rating_distribution.png"))
    plt_close(fig)
    logger.info("  Created rating_distribution.png")

    # Radar chart for top NGO
    top_ngo = ranked.iloc[0]
    kpi_cols = [
        "program_expense_ratio", "admin_expense_ratio",
        "fundraising_efficiency", "working_capital_ratio",
        "revenue_growth", "donor_dependency", "reserves_months",
    ]
    fig = plot_radar_chart(top_ngo, kpi_cols, top_ngo["ngo_name"],
                           str(fig_dir / "radar_top_ngo.png"))
    plt_close(fig)
    logger.info(f"  Created radar chart for {top_ngo['ngo_name']}")

    # Trend lines for top NGO
    trend_data = get_ngo_trend(df, top_ngo["ngo_name"])
    fig = plot_trend_lines(trend_data, top_ngo["ngo_name"], kpi_cols,
                           str(fig_dir / "trend_top_ngo.png"))
    plt_close(fig)
    logger.info(f"  Created trend chart for {top_ngo['ngo_name']}")

    # Rating counts summary
    rating_counts = df[df["year"] == latest_year]["overall_rating"].value_counts()
    logger.info(f"\nOverall Rating Distribution ({latest_year}):")
    for rating, count in rating_counts.items():
        logger.info(f"  {rating}: {count} NGOs")

    logger.info("\n" + "=" * 60)
    logger.info("Pipeline completed successfully!")
    logger.info("=" * 60)


def plt_close(fig):
    """Close a matplotlib figure."""
    import matplotlib.pyplot as plt
    plt.close(fig)


if __name__ == "__main__":
    main()
