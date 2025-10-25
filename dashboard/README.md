# A/B Testing Dashboard

Interactive Streamlit dashboard for analyzing the two-tier verification experiment.

## Features

- **Executive Summary**: Key metrics and recommendations at a glance
- **Metric Comparison**: Visual comparison of control vs treatment
- **Funnel Analysis**: User flow through verification tiers
- **Statistical Details**: Power analysis, SRM checks, effect sizes
- **CUPED Support**: Variance reduction toggle

## Running the Dashboard

### 1. Generate Sample Data

First, generate the synthetic data:

```bash
python scripts/generate_sample_data.py
```

This will create CSV files in the `data/` directory with 5,000 users and associated events.

### 2. Start the Dashboard

```bash
streamlit run dashboard/dashboard.py
```

The dashboard will open in your browser at `http://localhost:8501`

## Dashboard Sections

### Executive Summary
- Experiment status and duration
- Sample size validation
- Primary metric lift and p-value
- Ship/no-ship recommendation

### Key Metrics
- **Tier 1 (Email) Completion Rate**: Primary metric with statistical test results
- **Tier 2 (Badge/ID) Completion Rate**: Secondary metric analysis
- Interactive visualizations with confidence intervals

### Funnel Analysis
- Visual funnel showing user progression
- Drop-off rates at each stage
- Side-by-side comparison of control vs treatment

### Statistical Details
- Sample Ratio Mismatch (SRM) detection
- Power analysis and sample size validation
- Effect size calculations
- Confidence intervals

## Configuration

Dashboard settings can be adjusted in the sidebar:
- Experiment selection
- CUPED variance reduction toggle
- View experiment details and parameters

## Data Requirements

The dashboard expects the following CSV files in the `data/` directory:
- `users.csv`: User demographics
- `user_pre_metrics.csv`: Pre-experiment metrics for CUPED
- `experiment_assignments.csv`: Variant assignments
- `verification_attempts.csv`: Verification flow data

## Customization

To customize the dashboard:
- Edit `dashboard/dashboard.py` for layout changes
- Modify `.streamlit/config.toml` for theme settings
- Create components in `dashboard/components/` for reusable elements

## Performance

The dashboard uses Streamlit's caching (`@st.cache_data`) to optimize performance when loading large datasets.

## Troubleshooting

**Data not found error**: Run `python scripts/generate_sample_data.py` to generate sample data

**Import errors**: Ensure all dependencies are installed: `pip install -r requirements.txt`

**Port already in use**: Specify a different port: `streamlit run dashboard/dashboard.py --server.port 8502`
