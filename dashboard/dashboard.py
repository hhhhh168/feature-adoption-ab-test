"""
A/B Testing Dashboard
Interactive Streamlit dashboard for experiment analysis
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.statistical_analysis import ABTestAnalyzer
from src.cuped import CUPED
from src.config import EXP_CONFIG, ANALYSIS_CONFIG
from src.utils import calculate_conversion_rate, calculate_relative_lift

# Page configuration
st.set_page_config(
    page_title="A/B Test Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .big-font {
        font-size: 24px !important;
        font-weight: bold;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_sample_data():
    """Load sample data from CSV files"""
    try:
        data = {
            'users': pd.read_csv('data/users.csv'),
            'pre_metrics': pd.read_csv('data/user_pre_metrics.csv'),
            'assignments': pd.read_csv('data/experiment_assignments.csv'),
            'verification_attempts': pd.read_csv('data/verification_attempts.csv'),
        }
        return data
    except FileNotFoundError:
        st.error("Data files not found. Please generate data first by running: `python src/synthetic_data_generator.py`")
        return None


def create_metric_comparison_chart(metric_name, control_rate, treatment_rate, ci_lower, ci_upper):
    """Create comparison bar chart with error bars"""
    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Control',
        x=['Control'],
        y=[control_rate],
        marker_color='#89CFF0',
        text=[f'{control_rate:.2%}'],
        textposition='auto',
        textfont=dict(size=14, color='black')
    ))

    fig.add_trace(go.Bar(
        name='Treatment',
        x=['Treatment'],
        y=[treatment_rate],
        marker_color='#90EE90',
        text=[f'{treatment_rate:.2%}'],
        textposition='auto',
        textfont=dict(size=14, color='black'),
        error_y=dict(
            type='data',
            symmetric=False,
            array=[ci_upper - treatment_rate],
            arrayminus=[treatment_rate - ci_lower],
            color='#666'
        )
    ))

    fig.update_layout(
        title=f"{metric_name} Comparison",
        yaxis_title="Rate",
        yaxis_tickformat='.1%',
        showlegend=True,
        height=400,
        template="plotly_white"
    )

    return fig


def create_funnel_chart(funnel_data):
    """Create funnel visualization"""
    fig = go.Figure()

    for variant in ['control', 'treatment']:
        variant_data = funnel_data[funnel_data['variant'] == variant]

        fig.add_trace(go.Funnel(
            name=variant.capitalize(),
            y=variant_data['stage'],
            x=variant_data['users'],
            textinfo="value+percent initial",
            marker=dict(
                color='#89CFF0' if variant == 'control' else '#90EE90'
            )
        ))

    fig.update_layout(
        title="Verification Funnel by Variant",
        height=500,
        template="plotly_white"
    )

    return fig


def main():
    # Header
    st.title("Verification A/B Test Dashboard")
    st.markdown("**Two-Tier Verification Feature Optimization**")
    st.markdown("---")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")

        experiment_id = st.selectbox(
            "Experiment",
            [EXP_CONFIG.experiment_id],
            index=0
        )

        use_cuped = st.checkbox("Use CUPED Adjustment", value=True)

        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        This dashboard analyzes the two-tier verification experiment
        testing email domain + badge/ID verification flow optimization.

        **Key Metrics:**
        - Tier 1 (Email) completion rate
        - Tier 2 (Badge/ID) completion rate
        - User engagement metrics
        """)

        st.markdown("---")
        st.markdown("**Experiment Details:**")
        st.markdown(f"- Duration: {EXP_CONFIG.start_date} to {EXP_CONFIG.end_date}")
        st.markdown(f"- MDE: {EXP_CONFIG.mde:.0%}")
        st.markdown(f"- Alpha: {EXP_CONFIG.alpha}")
        st.markdown(f"- Power: {EXP_CONFIG.power}")

    # Load data
    with st.spinner("Loading experiment data..."):
        data = load_sample_data()

    if data is None:
        st.stop()

    # Initialize analyzer
    analyzer = ABTestAnalyzer(alpha=EXP_CONFIG.alpha, power=EXP_CONFIG.power)

    # Prepare analysis data
    verification_df = data['verification_attempts'].merge(
        data['assignments'][['user_id', 'variant']],
        on='user_id'
    )

    # === EXECUTIVE SUMMARY ===
    st.header("📊 Executive Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Experiment Status",
            "Active",
            "Day 14 of 14"
        )

    with col2:
        total_users = data['assignments']['variant'].value_counts().sum()
        st.metric(
            "Sample Size",
            f"{total_users:,}",
            "✅ Powered"
        )

    # Calculate Tier 1 results
    tier1_data = verification_df[verification_df['verification_tier'] == 1].copy()
    tier1_data['tier1_completed'] = (tier1_data['completion_status'] == 'completed').astype(int)

    tier1_by_variant = tier1_data.groupby('variant')['tier1_completed'].agg(['sum', 'count'])

    if len(tier1_by_variant) >= 2:
        tier1_result = analyzer.proportion_test(
            int(tier1_by_variant.loc['control', 'sum']),
            int(tier1_by_variant.loc['control', 'count']),
            int(tier1_by_variant.loc['treatment', 'sum']),
            int(tier1_by_variant.loc['treatment', 'count'])
        )

        with col3:
            delta_color = "normal" if tier1_result['statistically_significant'] else "off"
            st.metric(
                "Primary Metric Lift",
                f"{tier1_result['relative_lift']:.1%}",
                f"p={tier1_result['p_value']:.4f}",
                delta_color=delta_color
            )

        with col4:
            if tier1_result['statistically_significant'] and tier1_result['relative_lift'] > 0:
                recommendation = "🚀 SHIP"
                rec_text = "High confidence"
            else:
                recommendation = "⏸️ KEEP RUNNING"
                rec_text = "Need more data"

            st.metric(
                "Recommendation",
                recommendation,
                rec_text
            )

    st.markdown("---")

    # === KEY METRICS ===
    st.header("📈 Key Metrics")

    # Tier 1 Completion Rate
    with st.expander("📧 Tier 1 (Email) Completion Rate", expanded=True):
        if len(tier1_by_variant) >= 2:
            col1, col2, col3 = st.columns(3)

            with col1:
                st.subheader("Control")
                st.metric("Rate", f"{tier1_result['control_rate']:.2%}")
                st.caption(f"n={tier1_result['sample_size_control']:,}")

            with col2:
                st.subheader("Treatment")
                st.metric("Rate", f"{tier1_result['treatment_rate']:.2%}")
                st.caption(f"n={tier1_result['sample_size_treatment']:,}")

            with col3:
                st.subheader("Impact")
                delta_color = "normal" if tier1_result['statistically_significant'] else "off"
                st.metric(
                    "Relative Lift",
                    f"{tier1_result['relative_lift']:.2%}",
                    f"p={tier1_result['p_value']:.4f}",
                    delta_color=delta_color
                )
                st.caption(
                    f"95% CI: [{tier1_result['ci_lower']:.2%}, {tier1_result['ci_upper']:.2%}]"
                )

            # Visualization
            fig = create_metric_comparison_chart(
                "Tier 1 Completion",
                tier1_result['control_rate'],
                tier1_result['treatment_rate'],
                tier1_result['ci_lower'] + tier1_result['control_rate'],
                tier1_result['ci_upper'] + tier1_result['control_rate']
            )
            st.plotly_chart(fig, use_container_width=True)

    # Tier 2 Completion Rate
    tier2_data = verification_df[verification_df['verification_tier'] == 2].copy()
    tier2_data['tier2_completed'] = (tier2_data['completion_status'] == 'completed').astype(int)

    tier2_by_variant = tier2_data.groupby('variant')['tier2_completed'].agg(['sum', 'count'])

    if len(tier2_by_variant) >= 2:
        with st.expander("🆔 Tier 2 (Badge/ID) Completion Rate", expanded=True):
            tier2_result = analyzer.proportion_test(
                int(tier2_by_variant.loc['control', 'sum']),
                int(tier2_by_variant.loc['control', 'count']),
                int(tier2_by_variant.loc['treatment', 'sum']),
                int(tier2_by_variant.loc['treatment', 'count'])
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                st.subheader("Control")
                st.metric("Rate", f"{tier2_result['control_rate']:.2%}")
                st.caption(f"n={tier2_result['sample_size_control']:,}")

            with col2:
                st.subheader("Treatment")
                st.metric("Rate", f"{tier2_result['treatment_rate']:.2%}")
                st.caption(f"n={tier2_result['sample_size_treatment']:,}")

            with col3:
                st.subheader("Impact")
                delta_color = "normal" if tier2_result['statistically_significant'] else "off"
                st.metric(
                    "Relative Lift",
                    f"{tier2_result['relative_lift']:.2%}",
                    f"p={tier2_result['p_value']:.4f}",
                    delta_color=delta_color
                )
                st.caption(
                    f"95% CI: [{tier2_result['ci_lower']:.2%}, {tier2_result['ci_upper']:.2%}]"
                )

    st.markdown("---")

    # === FUNNEL ANALYSIS ===
    st.header("🎯 Verification Funnel")

    funnel_data = []
    for variant in ['control', 'treatment']:
        variant_users = data['assignments'][data['assignments']['variant'] == variant]['user_id'].nunique()

        tier1_started = tier1_data[tier1_data['variant'] == variant]['user_id'].nunique()
        tier1_completed = tier1_data[
            (tier1_data['variant'] == variant) &
            (tier1_data['completion_status'] == 'completed')
        ]['user_id'].nunique()

        tier2_completed = tier2_data[
            (tier2_data['variant'] == variant) &
            (tier2_data['completion_status'] == 'completed')
        ]['user_id'].nunique()

        funnel_data.extend([
            {'variant': variant, 'stage': 'Assigned', 'users': variant_users},
            {'variant': variant, 'stage': 'Tier 1 Started', 'users': tier1_started},
            {'variant': variant, 'stage': 'Tier 1 Complete', 'users': tier1_completed},
            {'variant': variant, 'stage': 'Tier 2 Complete', 'users': tier2_completed}
        ])

    funnel_df = pd.DataFrame(funnel_data)
    fig_funnel = create_funnel_chart(funnel_df)
    st.plotly_chart(fig_funnel, use_container_width=True)

    st.markdown("---")

    # === STATISTICAL DETAILS ===
    with st.expander("📊 Statistical Details & Quality Checks"):
        st.subheader("Sample Ratio Mismatch Check")

        variant_counts = data['assignments']['variant'].value_counts()
        srm_result = analyzer.check_sample_ratio_mismatch(
            variant_counts.get('control', 0),
            variant_counts.get('treatment', 0)
        )

        if srm_result['srm_detected']:
            st.error(f"⚠️ SRM DETECTED (p={srm_result['p_value']:.4f})")
        else:
            st.success(f"✅ No SRM detected (p={srm_result['p_value']:.4f})")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Control Users", f"{variant_counts.get('control', 0):,}")
        with col2:
            st.metric("Treatment Users", f"{variant_counts.get('treatment', 0):,}")
        with col3:
            st.metric("Observed Ratio", f"{srm_result['observed_ratio']:.2%}")

        st.markdown("---")

        st.subheader("Power Analysis")

        # Calculate required sample size
        required_n = analyzer.calculate_sample_size(
            baseline_rate=0.40,
            mde=0.15,
            alpha=0.05,
            power=0.80
        )

        # Calculate achieved power
        if len(tier1_by_variant) >= 2:
            achieved_power = analyzer.post_hoc_power(
                tier1_result['sample_size_control'],
                tier1_result['sample_size_treatment'],
                tier1_result['control_rate'],
                tier1_result['treatment_rate']
            )

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Required Sample Size", f"{required_n:,}")
            with col2:
                st.metric("Actual Sample Size", f"{tier1_result['sample_size_control']:,}")
            with col3:
                st.metric("Achieved Power", f"{achieved_power:.1%}")

        st.markdown("---")

        st.subheader("Effect Sizes")

        if len(tier1_by_variant) >= 2:
            st.markdown(f"""
            **Tier 1 Email Verification:**
            - Absolute Lift: {tier1_result['absolute_lift']:.2%}
            - Relative Lift: {tier1_result['relative_lift']:.2%}
            - Control Rate: {tier1_result['control_rate']:.2%}
            - Treatment Rate: {tier1_result['treatment_rate']:.2%}
            """)

        if len(tier2_by_variant) >= 2:
            st.markdown(f"""
            **Tier 2 Badge/ID Verification:**
            - Absolute Lift: {tier2_result['absolute_lift']:.2%}
            - Relative Lift: {tier2_result['relative_lift']:.2%}
            - Control Rate: {tier2_result['control_rate']:.2%}
            - Treatment Rate: {tier2_result['treatment_rate']:.2%}
            """)

    # === FOOTER ===
    st.markdown("---")
    st.markdown("*Dashboard built with Streamlit & Plotly*")


if __name__ == "__main__":
    main()
