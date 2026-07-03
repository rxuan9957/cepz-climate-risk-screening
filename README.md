# CEPZ Climate Risk Screening

Lightweight Streamlit prototype for screening climate risk across cultural-ecological protection zones (CEPZs).

The app is intended as an early planning tool: it combines simple hazard exposure indicators, cultural value, ecological sensitivity, adaptive capacity, and monitoring coverage into an explainable screening score. It is not a substitute for site-level climate modelling or expert assessment.

## Project Structure

```text
README.md
app.py
requirements.txt
data/sample_cepz.csv
outputs/demo_results.csv
figures/README.md
```

## Quick Start

1. Create and activate a Python environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the prototype:

```bash
streamlit run app.py
```

The app loads `data/sample_cepz.csv` by default. You can also upload a CSV with the same column structure.

## Input Data

Required columns:

| Column | Description |
| --- | --- |
| `zone_id` | Unique zone identifier |
| `zone_name` | Zone name |
| `province` | Province or region |
| `heritage_type` | Main cultural or ecological heritage category |
| `latitude`, `longitude` | Approximate centroid coordinates |
| `area_km2` | Area in square kilometers |
| `cultural_value_score` | 0-100 score for cultural importance |
| `ecological_sensitivity_score` | 0-100 score for ecological sensitivity |
| `flood_exposure` | 0-100 relative flood exposure |
| `heat_exposure` | 0-100 relative heat exposure |
| `drought_exposure` | 0-100 relative drought exposure |
| `wildfire_exposure` | 0-100 relative wildfire exposure |
| `storm_exposure` | 0-100 relative storm exposure |
| `adaptive_capacity` | 0-100 management and adaptation capacity |
| `monitoring_coverage` | 0-100 climate and conservation monitoring coverage |
| `notes` | Free-text planning note |

## Screening Logic

The prototype calculates:

- `exposure_index`: weighted average of selected climate hazards.
- `value_sensitivity_index`: average of cultural value and ecological sensitivity.
- `vulnerability_index`: inverse of adaptive capacity and monitoring coverage.
- `risk_score`: weighted combination of exposure, value/sensitivity, and vulnerability.
- `risk_class`: Low, Moderate, High, or Critical based on configurable thresholds.
- `priority_action`: practical next-step guidance based on the main risk drivers.

All weights and thresholds are adjustable in the Streamlit sidebar.

## Outputs

Use the app download button to export screened results as CSV. A demo output is included at `outputs/demo_results.csv`.

## Limitations

- The sample dataset is fictional and for demonstration only.
- Scores are normalized planning indicators, not observed probabilities.
- Results should be interpreted with local heritage, ecological, hydrological, and community expertise.
