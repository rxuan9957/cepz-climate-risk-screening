from __future__ import annotations

from io import StringIO
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
SAMPLE_DATA = BASE_DIR / "data" / "sample_cepz.csv"

REQUIRED_COLUMNS = [
    "zone_id",
    "zone_name",
    "province",
    "heritage_type",
    "latitude",
    "longitude",
    "area_km2",
    "cultural_value_score",
    "ecological_sensitivity_score",
    "flood_exposure",
    "heat_exposure",
    "drought_exposure",
    "wildfire_exposure",
    "storm_exposure",
    "adaptive_capacity",
    "monitoring_coverage",
    "notes",
]

HAZARD_COLUMNS = [
    "flood_exposure",
    "heat_exposure",
    "drought_exposure",
    "wildfire_exposure",
    "storm_exposure",
]


@st.cache_data
def load_sample_data() -> pd.DataFrame:
    return pd.read_csv(SAMPLE_DATA)


def validate_data(df: pd.DataFrame) -> list[str]:
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    errors = []
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}")

    numeric_columns = [
        "latitude",
        "longitude",
        "area_km2",
        "cultural_value_score",
        "ecological_sensitivity_score",
        "adaptive_capacity",
        "monitoring_coverage",
        *HAZARD_COLUMNS,
    ]
    present_numeric = [column for column in numeric_columns if column in df.columns]
    for column in present_numeric:
        if pd.to_numeric(df[column], errors="coerce").isna().any():
            errors.append(f"Column '{column}' contains non-numeric values.")

    return errors


def classify_risk(score: float, high_threshold: int, critical_threshold: int) -> str:
    if score >= critical_threshold:
        return "Critical"
    if score >= high_threshold:
        return "High"
    if score >= 40:
        return "Moderate"
    return "Low"


def recommend_action(row: pd.Series) -> str:
    hazard_columns = {
        "flood_exposure": "flood and drainage assessment",
        "heat_exposure": "heat stress adaptation plan",
        "drought_exposure": "water security and vegetation resilience review",
        "wildfire_exposure": "fire buffer and emergency access planning",
        "storm_exposure": "storm preparedness and infrastructure inspection",
    }
    top_hazard = max(hazard_columns, key=lambda column: row[column])

    if row["risk_class"] == "Critical":
        return f"Launch detailed assessment; prioritize {hazard_columns[top_hazard]}."
    if row["risk_class"] == "High":
        return f"Prepare targeted adaptation project; focus on {hazard_columns[top_hazard]}."
    if row["vulnerability_index"] >= 55:
        return "Strengthen monitoring, local response capacity, and maintenance routines."
    if row["risk_class"] == "Moderate":
        return "Track indicators annually and test low-regret adaptation options."
    return "Maintain routine monitoring and update screening when new climate data arrive."


def screen_risk(
    df: pd.DataFrame,
    hazard_weights: dict[str, float],
    exposure_weight: float,
    value_weight: float,
    vulnerability_weight: float,
    high_threshold: int,
    critical_threshold: int,
) -> pd.DataFrame:
    scored = df.copy()

    for column in REQUIRED_COLUMNS:
        if column in scored.columns and column not in {"zone_id", "zone_name", "province", "heritage_type", "notes"}:
            scored[column] = pd.to_numeric(scored[column], errors="coerce")

    hazard_weight_total = sum(hazard_weights.values()) or 1
    scored["exposure_index"] = sum(
        scored[column] * weight for column, weight in hazard_weights.items()
    ) / hazard_weight_total

    scored["value_sensitivity_index"] = (
        scored["cultural_value_score"] * 0.55
        + scored["ecological_sensitivity_score"] * 0.45
    )
    scored["vulnerability_index"] = (
        (100 - scored["adaptive_capacity"]) * 0.65
        + (100 - scored["monitoring_coverage"]) * 0.35
    )

    component_weight_total = exposure_weight + value_weight + vulnerability_weight
    if component_weight_total == 0:
        component_weight_total = 1

    scored["risk_score"] = (
        scored["exposure_index"] * exposure_weight
        + scored["value_sensitivity_index"] * value_weight
        + scored["vulnerability_index"] * vulnerability_weight
    ) / component_weight_total
    scored["risk_score"] = scored["risk_score"].round(1)

    scored["risk_class"] = scored["risk_score"].apply(
        classify_risk,
        high_threshold=high_threshold,
        critical_threshold=critical_threshold,
    )
    scored["priority_action"] = scored.apply(recommend_action, axis=1)

    return scored.sort_values("risk_score", ascending=False)


def render_sidebar() -> tuple[dict[str, float], float, float, float, int, int]:
    st.sidebar.header("Screening settings")

    st.sidebar.subheader("Hazard weights")
    hazard_weights = {
        "flood_exposure": st.sidebar.slider("Flood", 0.0, 3.0, 1.2, 0.1),
        "heat_exposure": st.sidebar.slider("Heat", 0.0, 3.0, 1.0, 0.1),
        "drought_exposure": st.sidebar.slider("Drought", 0.0, 3.0, 1.0, 0.1),
        "wildfire_exposure": st.sidebar.slider("Wildfire", 0.0, 3.0, 0.8, 0.1),
        "storm_exposure": st.sidebar.slider("Storm", 0.0, 3.0, 0.9, 0.1),
    }

    st.sidebar.subheader("Risk component weights")
    exposure_weight = st.sidebar.slider("Exposure", 0.0, 1.0, 0.45, 0.05)
    value_weight = st.sidebar.slider("Cultural/ecological value", 0.0, 1.0, 0.35, 0.05)
    vulnerability_weight = st.sidebar.slider("Vulnerability", 0.0, 1.0, 0.20, 0.05)

    st.sidebar.subheader("Class thresholds")
    high_threshold = st.sidebar.slider("High risk starts at", 40, 90, 65, 1)
    critical_threshold = st.sidebar.slider("Critical risk starts at", high_threshold + 1, 100, 80, 1)

    return (
        hazard_weights,
        exposure_weight,
        value_weight,
        vulnerability_weight,
        high_threshold,
        critical_threshold,
    )


def render_metrics(scored: pd.DataFrame) -> None:
    high_or_critical = scored[scored["risk_class"].isin(["High", "Critical"])]
    highest = scored.iloc[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Zones screened", f"{len(scored):,}")
    col2.metric("High or critical", f"{len(high_or_critical):,}")
    col3.metric("Mean risk score", f"{scored['risk_score'].mean():.1f}")
    col4.metric("Top priority", highest["zone_name"], f"{highest['risk_score']:.1f}")


def render_map(scored: pd.DataFrame) -> None:
    color_map = {
        "Low": "#2ca25f",
        "Moderate": "#f0c419",
        "High": "#f28e2b",
        "Critical": "#d62728",
    }
    fig = px.scatter_mapbox(
        scored,
        lat="latitude",
        lon="longitude",
        color="risk_class",
        size="risk_score",
        hover_name="zone_name",
        hover_data={
            "province": True,
            "heritage_type": True,
            "risk_score": ":.1f",
            "exposure_index": ":.1f",
            "value_sensitivity_index": ":.1f",
            "vulnerability_index": ":.1f",
            "latitude": False,
            "longitude": False,
        },
        color_discrete_map=color_map,
        zoom=3,
        height=480,
    )
    fig.update_layout(
        mapbox_style="carto-positron",
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        legend_title_text="Risk class",
    )
    st.plotly_chart(fig, use_container_width=True)


def render_charts(scored: pd.DataFrame) -> None:
    left, right = st.columns((1.15, 0.85))

    top_n = scored.head(10).sort_values("risk_score")
    bar = px.bar(
        top_n,
        x="risk_score",
        y="zone_name",
        color="risk_class",
        orientation="h",
        labels={"risk_score": "Risk score", "zone_name": ""},
        color_discrete_map={
            "Low": "#2ca25f",
            "Moderate": "#f0c419",
            "High": "#f28e2b",
            "Critical": "#d62728",
        },
        height=420,
    )
    bar.update_layout(margin={"l": 0, "r": 10, "t": 20, "b": 0}, showlegend=False)
    left.plotly_chart(bar, use_container_width=True)

    risk_counts = (
        scored["risk_class"]
        .value_counts()
        .reindex(["Low", "Moderate", "High", "Critical"])
        .fillna(0)
        .reset_index()
    )
    risk_counts.columns = ["risk_class", "count"]
    donut = px.pie(
        risk_counts,
        values="count",
        names="risk_class",
        hole=0.55,
        color="risk_class",
        color_discrete_map={
            "Low": "#2ca25f",
            "Moderate": "#f0c419",
            "High": "#f28e2b",
            "Critical": "#d62728",
        },
        height=420,
    )
    donut.update_layout(margin={"l": 0, "r": 0, "t": 20, "b": 0}, legend_title_text="")
    right.plotly_chart(donut, use_container_width=True)


def to_csv_download(df: pd.DataFrame) -> bytes:
    buffer = StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8")


def main() -> None:
    st.set_page_config(
        page_title="CEPZ Climate Risk Screening",
        page_icon="CE",
        layout="wide",
    )

    st.title("CEPZ Climate Risk Screening")
    st.caption("Prototype dashboard for rapid climate risk triage of cultural-ecological protection zones.")

    settings = render_sidebar()

    uploaded_file = st.file_uploader("Upload CEPZ CSV", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.info("Using uploaded dataset.")
    else:
        df = load_sample_data()
        st.info("Using bundled sample dataset from data/sample_cepz.csv.")

    errors = validate_data(df)
    if errors:
        st.error("The dataset cannot be screened yet.")
        for error in errors:
            st.write(f"- {error}")
        st.stop()

    scored = screen_risk(df, *settings)

    with st.expander("Filters", expanded=True):
        col1, col2, col3 = st.columns(3)
        provinces = col1.multiselect(
            "Province or region",
            sorted(scored["province"].unique()),
            default=sorted(scored["province"].unique()),
        )
        risk_classes = col2.multiselect(
            "Risk class",
            ["Low", "Moderate", "High", "Critical"],
            default=["Low", "Moderate", "High", "Critical"],
        )
        min_score = col3.slider("Minimum risk score", 0, 100, 0)

    filtered = scored[
        scored["province"].isin(provinces)
        & scored["risk_class"].isin(risk_classes)
        & (scored["risk_score"] >= min_score)
    ]

    if filtered.empty:
        st.warning("No zones match the current filters.")
        st.stop()

    render_metrics(filtered)

    tab_map, tab_charts, tab_table, tab_method = st.tabs(
        ["Risk map", "Priority charts", "Screening table", "Method"]
    )

    with tab_map:
        render_map(filtered)

    with tab_charts:
        render_charts(filtered)

    with tab_table:
        display_columns = [
            "zone_id",
            "zone_name",
            "province",
            "heritage_type",
            "risk_score",
            "risk_class",
            "exposure_index",
            "value_sensitivity_index",
            "vulnerability_index",
            "priority_action",
        ]
        st.dataframe(
            filtered[display_columns],
            use_container_width=True,
            hide_index=True,
        )
        st.download_button(
            "Download screened results",
            data=to_csv_download(filtered),
            file_name="cepz_screened_results.csv",
            mime="text/csv",
        )

    with tab_method:
        st.markdown(
            """
            The screening score is an adjustable weighted index:

            - Exposure combines flood, heat, drought, wildfire, and storm indicators.
            - Cultural/ecological value combines cultural value and ecological sensitivity.
            - Vulnerability increases where adaptive capacity and monitoring coverage are lower.

            Risk classes are based on the sidebar thresholds. Use this prototype for comparative triage and scoping of deeper assessments.
            """
        )


if __name__ == "__main__":
    main()
