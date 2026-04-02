"""NGO Financial Health Scorecard -- Streamlit Dashboard.

Self-contained app: generates synthetic data, computes KPIs and health
scores, then renders an interactive dashboard with Plotly charts.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="NGO Financial Health Scorecard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Data generation (mirrors src/data/generate_dataset.py)
# ---------------------------------------------------------------------------
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

DEFAULT_THRESHOLDS = {
    "program_expense_ratio": {"green": 0.75, "yellow": 0.65, "higher_is_better": True},
    "admin_expense_ratio":   {"green": 0.15, "yellow": 0.25, "higher_is_better": False},
    "fundraising_efficiency": {"green": 0.10, "yellow": 0.20, "higher_is_better": False},
    "working_capital_ratio": {"green": 1.5,  "yellow": 1.0,  "higher_is_better": True},
    "revenue_growth":        {"green": 0.05, "yellow": 0.0,  "higher_is_better": True},
    "donor_dependency":      {"green": 0.50, "yellow": 0.75, "higher_is_better": False},
    "reserves_months":       {"green": 6.0,  "yellow": 3.0,  "higher_is_better": True},
}

DEFAULT_WEIGHTS = {
    "program_expense_ratio": 0.20,
    "admin_expense_ratio":   0.10,
    "fundraising_efficiency": 0.15,
    "working_capital_ratio": 0.15,
    "revenue_growth":        0.10,
    "donor_dependency":      0.15,
    "reserves_months":       0.15,
}

KPI_COLS = list(DEFAULT_THRESHOLDS.keys())

KPI_LABELS = {k: k.replace("_", " ").title() for k in KPI_COLS}

RATING_COLORS = {"Green": "#2ecc71", "Yellow": "#f1c40f", "Red": "#e74c3c", "N/A": "#bdc3c7"}


# ---------------------------------------------------------------------------
# Cached helpers
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Generating NGO financial data ...")
def generate_data(num_ngos: int = 20, num_years: int = 5, start_year: int = 2021, seed: int = 42) -> pd.DataFrame:
    rng = np.random.RandomState(seed)
    records = []
    for i in range(min(num_ngos, len(NGO_NAMES))):
        name = NGO_NAMES[i]
        sector = NGO_SECTORS[i]
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
            donor_revenue = total_revenue * donor_share * rng.uniform(0.90, 1.10)
            grant_revenue = total_revenue * rng.uniform(0.05, 0.30)
            earned_revenue = max(0, total_revenue - donor_revenue - grant_revenue)
            actual_total_revenue = donor_revenue + grant_revenue + earned_revenue
            prog_expense = actual_total_revenue * program_ratio * rng.uniform(0.92, 1.08)
            admin_expense = actual_total_revenue * admin_ratio * rng.uniform(0.90, 1.10)
            fundraising_expense = actual_total_revenue * rng.uniform(0.03, 0.15)
            total_expenses = prog_expense + admin_expense + fundraising_expense
            current_assets = actual_total_revenue * rng.uniform(0.20, 0.80)
            current_liabilities = current_assets * rng.uniform(0.20, 0.90)
            total_assets = current_assets + actual_total_revenue * rng.uniform(0.10, 0.50)
            net_assets = total_assets - current_liabilities - actual_total_revenue * rng.uniform(0.0, 0.15)
            cash_reserves = current_assets * rng.uniform(0.30, 0.80)
            monthly_operating = total_expenses / 12.0
            records.append({
                "ngo_name": name, "sector": sector, "year": year,
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
    return pd.DataFrame(records)


@st.cache_data(show_spinner="Computing KPIs and health scores ...")
def compute_scores(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["program_expense_ratio"] = (result["program_expenses"] / result["total_expenses"]).round(4)
    result["admin_expense_ratio"] = (result["admin_expenses"] / result["total_expenses"]).round(4)
    result["fundraising_efficiency"] = (result["fundraising_expenses"] / result["total_revenue"]).round(4)
    result["working_capital_ratio"] = (result["current_assets"] / result["current_liabilities"]).round(4)
    result = result.sort_values(["ngo_name", "year"])
    result["revenue_growth"] = result.groupby("ngo_name")["total_revenue"].pct_change().round(4)
    result["donor_dependency"] = (result["donor_revenue"] / result["total_revenue"]).round(4)
    result["reserves_months"] = (result["cash_reserves"] / result["monthly_operating_expenses"]).round(2)

    # Ratings
    for kpi, t in DEFAULT_THRESHOLDS.items():
        hib = t["higher_is_better"]
        g, y = t["green"], t["yellow"]

        def _rate(v, _g=g, _y=y, _h=hib):
            if pd.isna(v):
                return "N/A"
            if _h:
                return "Green" if v >= _g else ("Yellow" if v >= _y else "Red")
            else:
                return "Green" if v <= _g else ("Yellow" if v <= _y else "Red")

        result[f"{kpi}_rating"] = result[kpi].apply(_rate)
        result[f"{kpi}_score"] = result[f"{kpi}_rating"].map(
            {"Green": 3.0, "Yellow": 2.0, "Red": 1.0, "N/A": 0.0}
        )

    total_w = sum(DEFAULT_WEIGHTS.values())
    result["overall_score"] = sum(
        result[f"{k}_score"] * (w / total_w) for k, w in DEFAULT_WEIGHTS.items()
    ).round(3)
    result["overall_rating"] = result["overall_score"].apply(
        lambda s: "Green" if s >= 2.5 else ("Yellow" if s >= 1.75 else "Red")
    )
    return result


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
raw_df = generate_data()
scored_df = compute_scores(raw_df)
latest_year = int(scored_df["year"].max())
years = sorted(scored_df["year"].unique())

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.title("NGO Financial Scorecard")
st.sidebar.markdown("---")
selected_year = st.sidebar.selectbox("Select Year", years, index=len(years) - 1)
ngo_list = sorted(scored_df["ngo_name"].unique())
selected_ngo = st.sidebar.selectbox("Select NGO", ngo_list)

st.sidebar.markdown("---")
st.sidebar.caption("Data is synthetically generated for demonstration purposes.")

# ---------------------------------------------------------------------------
# Filtered frames
# ---------------------------------------------------------------------------
year_df = scored_df[scored_df["year"] == selected_year].copy()
year_df = year_df.sort_values("overall_score", ascending=False).reset_index(drop=True)
year_df["rank"] = range(1, len(year_df) + 1)

ngo_trend = scored_df[scored_df["ngo_name"] == selected_ngo].sort_values("year")
ngo_year = year_df[year_df["ngo_name"] == selected_ngo]

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("NGO Financial Health Scorecard")
st.markdown(f"**Year: {selected_year}** | Evaluating **{len(ngo_list)} NGOs** across 7 financial KPIs")
st.markdown("---")

# ---------------------------------------------------------------------------
# Top-level metrics
# ---------------------------------------------------------------------------
green_count = int((year_df["overall_rating"] == "Green").sum())
yellow_count = int((year_df["overall_rating"] == "Yellow").sum())
red_count = int((year_df["overall_rating"] == "Red").sum())
avg_score = round(year_df["overall_score"].mean(), 2)

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total NGOs", len(year_df))
col2.metric("Avg Health Score", f"{avg_score} / 3.0")
col3.metric("Healthy (Green)", green_count)
col4.metric("Caution (Yellow)", yellow_count)
col5.metric("At Risk (Red)", red_count)

st.markdown("---")

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_overview, tab_compare, tab_ngo, tab_table = st.tabs(
    ["Overview", "KPI Comparison", f"NGO Detail: {selected_ngo}", "Full Data Table"]
)

# ===================== TAB 1: Overview =====================================
with tab_overview:
    ov_col1, ov_col2 = st.columns([3, 2])

    with ov_col1:
        st.subheader("Health Rankings")
        fig_rank = go.Figure()
        fig_rank.add_trace(go.Bar(
            y=year_df["ngo_name"],
            x=year_df["overall_score"],
            orientation="h",
            marker_color=[RATING_COLORS.get(r, "#95a5a6") for r in year_df["overall_rating"]],
            text=[f"{s:.2f} ({r})" for s, r in zip(year_df["overall_score"], year_df["overall_rating"])],
            textposition="outside",
        ))
        fig_rank.update_layout(
            xaxis_title="Overall Health Score",
            xaxis_range=[0, 3.4],
            yaxis=dict(autorange="reversed"),
            height=600,
            margin=dict(l=10, r=10, t=10, b=30),
        )
        st.plotly_chart(fig_rank, use_container_width=True)

    with ov_col2:
        st.subheader("Health Rating Distribution")
        dist_data = pd.DataFrame({
            "Rating": ["Green", "Yellow", "Red"],
            "Count": [green_count, yellow_count, red_count],
        })
        fig_pie = px.pie(
            dist_data, values="Count", names="Rating",
            color="Rating",
            color_discrete_map=RATING_COLORS,
            hole=0.4,
        )
        fig_pie.update_traces(textinfo="label+value+percent", textfont_size=13)
        fig_pie.update_layout(height=400, margin=dict(t=10, b=10))
        st.plotly_chart(fig_pie, use_container_width=True)

        # KPI averages card
        st.subheader("KPI Averages")
        for kpi in KPI_COLS:
            val = year_df[kpi].mean()
            label = KPI_LABELS[kpi]
            if kpi == "reserves_months":
                st.markdown(f"**{label}:** {val:.1f} months")
            elif kpi in ("working_capital_ratio",):
                st.markdown(f"**{label}:** {val:.2f}x")
            else:
                st.markdown(f"**{label}:** {val:.1%}")

# ===================== TAB 2: KPI Comparison ===============================
with tab_compare:
    st.subheader(f"KPI Comparison Across All NGOs ({selected_year})")
    selected_kpi = st.selectbox("Choose a KPI", KPI_COLS, format_func=lambda k: KPI_LABELS[k])

    kpi_sorted = year_df.sort_values(selected_kpi, ascending=False)
    t = DEFAULT_THRESHOLDS[selected_kpi]

    fig_kpi = go.Figure()
    fig_kpi.add_trace(go.Bar(
        x=kpi_sorted["ngo_name"],
        y=kpi_sorted[selected_kpi],
        marker_color=[RATING_COLORS.get(r, "#95a5a6") for r in kpi_sorted[f"{selected_kpi}_rating"]],
        text=kpi_sorted[selected_kpi].round(3),
        textposition="outside",
    ))
    # Threshold lines
    fig_kpi.add_hline(y=t["green"], line_dash="dash", line_color="#2ecc71",
                      annotation_text="Green threshold", annotation_position="top left")
    fig_kpi.add_hline(y=t["yellow"], line_dash="dash", line_color="#f1c40f",
                      annotation_text="Yellow threshold", annotation_position="bottom left")
    fig_kpi.update_layout(
        xaxis_tickangle=-45, height=500,
        yaxis_title=KPI_LABELS[selected_kpi],
        margin=dict(t=10, b=10),
    )
    st.plotly_chart(fig_kpi, use_container_width=True)

    # Rating breakdown per KPI (grouped bar)
    st.subheader("Rating Breakdown by KPI")
    rating_records = []
    for kpi in KPI_COLS:
        for rating in ["Green", "Yellow", "Red"]:
            cnt = int((year_df[f"{kpi}_rating"] == rating).sum())
            rating_records.append({"KPI": KPI_LABELS[kpi], "Rating": rating, "Count": cnt})
    rating_breakdown = pd.DataFrame(rating_records)
    fig_rb = px.bar(
        rating_breakdown, x="KPI", y="Count", color="Rating",
        barmode="group",
        color_discrete_map=RATING_COLORS,
    )
    fig_rb.update_layout(xaxis_tickangle=-30, height=400, margin=dict(t=10, b=10))
    st.plotly_chart(fig_rb, use_container_width=True)

# ===================== TAB 3: Individual NGO ===============================
with tab_ngo:
    if ngo_year.empty:
        st.warning(f"No data for {selected_ngo} in {selected_year}.")
    else:
        ngo_row = ngo_year.iloc[0]

        # Header metrics
        st.subheader(f"{selected_ngo}  --  {ngo_row['sector']}")
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("Overall Score", f"{ngo_row['overall_score']:.2f} / 3.0")
        mc2.metric("Overall Rating", ngo_row["overall_rating"])
        mc3.metric("Rank", f"#{int(ngo_row['rank'])} of {len(year_df)}")
        mc4.metric("Total Revenue", f"${ngo_row['total_revenue']:,.0f}")

        st.markdown("---")

        # Radar chart
        r_col1, r_col2 = st.columns([3, 2])
        with r_col1:
            st.subheader("KPI Radar")
            radar_vals = [ngo_row[f"{k}_score"] for k in KPI_COLS]
            radar_labels = [KPI_LABELS[k] for k in KPI_COLS]
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=radar_vals + [radar_vals[0]],
                theta=radar_labels + [radar_labels[0]],
                fill="toself",
                fillcolor="rgba(41,128,185,0.25)",
                line_color="#2980b9",
                name=selected_ngo,
            ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 3.5],
                                           tickvals=[1, 2, 3], ticktext=["Red", "Yellow", "Green"])),
                showlegend=False, height=420, margin=dict(t=30, b=30),
            )
            st.plotly_chart(fig_radar, use_container_width=True)

        with r_col2:
            st.subheader("KPI Ratings")
            for kpi in KPI_COLS:
                val = ngo_row[kpi]
                rating = ngo_row[f"{kpi}_rating"]
                color = RATING_COLORS.get(rating, "#bdc3c7")
                if kpi == "reserves_months":
                    fmt_val = f"{val:.1f} mo"
                elif kpi == "working_capital_ratio":
                    fmt_val = f"{val:.2f}x"
                else:
                    fmt_val = f"{val:.1%}"
                st.markdown(
                    f"<span style='display:inline-block;width:12px;height:12px;"
                    f"border-radius:50%;background:{color};margin-right:6px;'></span>"
                    f"**{KPI_LABELS[kpi]}:** {fmt_val} ({rating})",
                    unsafe_allow_html=True,
                )

        st.markdown("---")

        # Trend analysis
        st.subheader(f"Trend Analysis: {selected_ngo} ({years[0]}--{years[-1]})")
        trend_kpi = st.selectbox("KPI for Trend", KPI_COLS, format_func=lambda k: KPI_LABELS[k], key="trend_kpi")
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=ngo_trend["year"], y=ngo_trend[trend_kpi],
            mode="lines+markers+text",
            text=ngo_trend[trend_kpi].round(3).astype(str),
            textposition="top center",
            line=dict(color="#2980b9", width=3),
            marker=dict(size=9),
        ))
        # Add threshold bands
        t = DEFAULT_THRESHOLDS[trend_kpi]
        fig_trend.add_hline(y=t["green"], line_dash="dot", line_color="#2ecc71", annotation_text="Green")
        fig_trend.add_hline(y=t["yellow"], line_dash="dot", line_color="#f1c40f", annotation_text="Yellow")
        fig_trend.update_layout(
            xaxis_title="Year", yaxis_title=KPI_LABELS[trend_kpi],
            height=380, margin=dict(t=10, b=10),
        )
        st.plotly_chart(fig_trend, use_container_width=True)

        # Multi-KPI trend (small multiples)
        st.subheader("All KPI Trends")
        trend_cols = st.columns(2)
        for idx, kpi in enumerate(KPI_COLS):
            with trend_cols[idx % 2]:
                fig_sm = go.Figure()
                fig_sm.add_trace(go.Scatter(
                    x=ngo_trend["year"], y=ngo_trend[kpi],
                    mode="lines+markers", line=dict(color="#2980b9", width=2),
                    marker=dict(size=6),
                ))
                fig_sm.update_layout(
                    title=dict(text=KPI_LABELS[kpi], font=dict(size=13)),
                    height=250, margin=dict(l=40, r=20, t=35, b=30),
                    xaxis=dict(dtick=1), yaxis_title="",
                )
                st.plotly_chart(fig_sm, use_container_width=True)

# ===================== TAB 4: Data Table ===================================
with tab_table:
    st.subheader(f"All NGO Scores -- {selected_year}")
    display_cols = ["rank", "ngo_name", "sector", "overall_score", "overall_rating"] + \
                   [k for k in KPI_COLS] + [f"{k}_rating" for k in KPI_COLS]
    table_df = year_df[display_cols].copy()
    table_df.columns = (
        ["Rank", "NGO Name", "Sector", "Overall Score", "Overall Rating"]
        + [KPI_LABELS[k] for k in KPI_COLS]
        + [f"{KPI_LABELS[k]} Rating" for k in KPI_COLS]
    )

    def _color_rating(val):
        colors = {"Green": "background-color: #d5f5e3", "Yellow": "background-color: #fef9e7",
                  "Red": "background-color: #fadbd8", "N/A": ""}
        return colors.get(val, "")

    rating_display_cols = ["Overall Rating"] + [f"{KPI_LABELS[k]} Rating" for k in KPI_COLS]
    try:
        styled = table_df.style.map(_color_rating, subset=rating_display_cols).format(precision=4)
    except AttributeError:
        styled = table_df.style.applymap(_color_rating, subset=rating_display_cols).format(precision=4)
    st.dataframe(styled, use_container_width=True, height=650)

    st.download_button(
        "Download CSV",
        data=table_df.to_csv(index=False).encode("utf-8"),
        file_name=f"ngo_scorecard_{selected_year}.csv",
        mime="text/csv",
    )
