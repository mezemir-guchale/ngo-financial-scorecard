# NGO Financial Health Scorecard

A data-driven framework for evaluating the financial health of non-governmental organizations using key performance indicators (KPIs). This tool generates a comprehensive scorecard with Red/Yellow/Green ratings, rankings, and visualizations to help stakeholders assess organizational sustainability.

## Author

**Mezemir Neway Guchale**
- Email: gumezemir@gmail.com
- LinkedIn: [linkedin.com/in/mezemir-guchale](https://linkedin.com/in/mezemir-guchale)

## Project Overview

This project analyzes synthetic financial data for 20 NGOs over 5 years, computing seven critical financial KPIs:

| KPI | Description | Green | Yellow | Red |
|-----|-------------|-------|--------|-----|
| Program Expense Ratio | % of expenses going to programs | >= 75% | 65-75% | < 65% |
| Admin Expense Ratio | % of expenses on administration | <= 15% | 15-25% | > 25% |
| Fundraising Efficiency | Cost to raise $1 | <= 10% | 10-20% | > 20% |
| Working Capital Ratio | Current assets / liabilities | >= 1.5 | 1.0-1.5 | < 1.0 |
| Revenue Growth | Year-over-year revenue change | >= 5% | 0-5% | < 0% |
| Donor Dependency | Donor revenue / total revenue | <= 50% | 50-75% | > 75% |
| Reserves (Months) | Cash reserves / monthly expenses | >= 6 | 3-6 | < 3 |

## Project Structure

```
05-ngo-financial-scorecard/
├── configs/config.yaml          # Configuration parameters
├── scripts/run_pipeline.py      # Main pipeline script
├── src/
│   ├── data/
│   │   ├── generate_dataset.py  # Synthetic data generation
│   │   └── loader.py            # Data loading utilities
│   ├── analysis/
│   │   └── scorecard.py         # KPI computation and scoring
│   ├── visualization/
│   │   └── charts.py            # Bar charts, radar charts, trends
│   └── utils/
│       ├── config.py            # Configuration loader
│       └── logger.py            # Logging setup
├── tests/
│   └── test_scorecard.py        # Unit tests (20+ tests)
├── data/                        # Generated data (raw and processed)
├── reports/                     # Output figures and logs
├── notebooks/                   # Jupyter notebooks
├── requirements.txt
├── setup.py
└── README.md
```

## Setup and Usage

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the full pipeline
python scripts/run_pipeline.py

# Run tests
pytest tests/ -v
```

## Output

The pipeline generates:
- **CSV files**: Raw and processed data with KPIs and scores
- **Health Rankings**: Horizontal bar chart showing all NGOs ranked by score
- **Radar Charts**: Spider plots of individual NGO KPI profiles
- **Trend Lines**: Year-over-year KPI tracking
- **Rating Distribution**: Grouped bar chart of Green/Yellow/Red counts per KPI

## Methodology

Each KPI is assigned a rating (Green=3, Yellow=2, Red=1) based on configurable thresholds. The overall health score is a weighted average of individual KPI scores. NGOs are then ranked from healthiest to most at-risk.

## License

MIT License
