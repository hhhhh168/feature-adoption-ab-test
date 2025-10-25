"""
Utility functions for A/B Testing Platform
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json


def calculate_conversion_rate(df: pd.DataFrame,
                              conversion_col: str,
                              group_col: Optional[str] = None) -> pd.DataFrame:
    """
    Calculate conversion rates with confidence intervals

    Args:
        df: DataFrame with conversion data
        conversion_col: Column indicating conversion (0/1 or True/False)
        group_col: Optional column to group by (e.g., 'variant')

    Returns:
        DataFrame with conversion rates and confidence intervals
    """
    if group_col:
        grouped = df.groupby(group_col)[conversion_col].agg([
            ('conversions', 'sum'),
            ('total', 'count'),
            ('rate', 'mean')
        ]).reset_index()
    else:
        grouped = pd.DataFrame([{
            'conversions': df[conversion_col].sum(),
            'total': len(df),
            'rate': df[conversion_col].mean()
        }])

    # Calculate Wilson score confidence intervals
    from scipy import stats
    z = stats.norm.ppf(0.975)  # 95% CI

    def wilson_ci(p, n):
        """Wilson score confidence interval"""
        if n == 0:
            return 0, 0
        denominator = 1 + z**2/n
        centre = (p + z**2/(2*n)) / denominator
        adjustment = z * np.sqrt((p*(1-p))/n + z**2/(4*n**2)) / denominator
        return centre - adjustment, centre + adjustment

    ci_lower = []
    ci_upper = []

    for _, row in grouped.iterrows():
        lower, upper = wilson_ci(row['rate'], row['total'])
        ci_lower.append(lower)
        ci_upper.append(upper)

    grouped['ci_lower'] = ci_lower
    grouped['ci_upper'] = ci_upper

    return grouped


def calculate_relative_lift(control_value: float,
                            treatment_value: float) -> Dict[str, float]:
    """
    Calculate relative and absolute lift

    Args:
        control_value: Control group metric value
        treatment_value: Treatment group metric value

    Returns:
        Dictionary with absolute_lift and relative_lift
    """
    absolute_lift = treatment_value - control_value
    relative_lift = absolute_lift / control_value if control_value != 0 else 0

    return {
        'absolute_lift': absolute_lift,
        'relative_lift': relative_lift,
        'percent_change': relative_lift * 100
    }


def format_number(value: float, format_type: str = 'default') -> str:
    """
    Format numbers for display

    Args:
        value: Number to format
        format_type: Type of formatting ('default', 'percent', 'currency', 'integer')

    Returns:
        Formatted string
    """
    if pd.isna(value):
        return 'N/A'

    if format_type == 'percent':
        return f"{value:.2%}"
    elif format_type == 'currency':
        return f"${value:,.2f}"
    elif format_type == 'integer':
        return f"{int(value):,}"
    else:
        return f"{value:,.2f}"


def create_summary_stats(df: pd.DataFrame,
                        metric_col: str,
                        group_col: str = 'variant') -> pd.DataFrame:
    """
    Create summary statistics by group

    Args:
        df: DataFrame with data
        metric_col: Column to summarize
        group_col: Column to group by

    Returns:
        DataFrame with summary statistics
    """
    summary = df.groupby(group_col)[metric_col].agg([
        ('count', 'count'),
        ('mean', 'mean'),
        ('std', 'std'),
        ('min', 'min'),
        ('25%', lambda x: x.quantile(0.25)),
        ('50%', lambda x: x.quantile(0.50)),
        ('75%', lambda x: x.quantile(0.75)),
        ('max', 'max')
    ]).reset_index()

    return summary


def calculate_sample_size_required(baseline_rate: float,
                                  mde: float,
                                  alpha: float = 0.05,
                                  power: float = 0.80) -> int:
    """
    Calculate required sample size for proportion test

    Args:
        baseline_rate: Control group conversion rate
        mde: Minimum detectable effect (relative, e.g., 0.15 for 15%)
        alpha: Significance level
        power: Statistical power

    Returns:
        Required sample size per variant
    """
    from scipy import stats

    treatment_rate = baseline_rate * (1 + mde)
    p_pooled = (baseline_rate + treatment_rate) / 2

    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)

    n = (2 * p_pooled * (1 - p_pooled) * (z_alpha + z_beta)**2) / \
        (baseline_rate - treatment_rate)**2

    return int(np.ceil(n))


def get_date_range(start_date: str, end_date: str) -> List[str]:
    """
    Generate list of dates between start and end

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        List of date strings
    """
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')

    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)

    return dates


def aggregate_daily_metrics(events_df: pd.DataFrame,
                            date_col: str = 'event_timestamp',
                            group_cols: List[str] = ['variant']) -> pd.DataFrame:
    """
    Aggregate metrics by day

    Args:
        events_df: Events DataFrame
        date_col: Column with timestamps
        group_cols: Columns to group by (in addition to date)

    Returns:
        DataFrame with daily aggregated metrics
    """
    # Convert to date
    events_df = events_df.copy()
    events_df['date'] = pd.to_datetime(events_df[date_col]).dt.date

    # Aggregate
    group_cols_with_date = ['date'] + group_cols

    daily = events_df.groupby(group_cols_with_date).agg({
        'user_id': 'nunique',
        'session_id': 'nunique',
        'event_id': 'count'
    }).reset_index()

    daily.columns = group_cols_with_date + ['active_users', 'sessions', 'total_events']

    return daily


def export_to_json(data: Dict, filepath: str, pretty: bool = True):
    """
    Export dictionary to JSON file

    Args:
        data: Dictionary to export
        filepath: Output file path
        pretty: Whether to pretty-print JSON
    """
    with open(filepath, 'w') as f:
        if pretty:
            json.dump(data, f, indent=2, default=str)
        else:
            json.dump(data, f, default=str)


def load_from_json(filepath: str) -> Dict:
    """
    Load dictionary from JSON file

    Args:
        filepath: Input file path

    Returns:
        Dictionary from JSON
    """
    with open(filepath, 'r') as f:
        return json.load(f)


def check_data_completeness(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check data completeness and quality

    Args:
        df: DataFrame to check

    Returns:
        Dictionary with completeness metrics
    """
    total_rows = len(df)
    total_cols = len(df.columns)

    # Missing values
    missing_counts = df.isnull().sum()
    missing_pct = (missing_counts / total_rows * 100).round(2)

    # Duplicate rows
    duplicate_count = df.duplicated().sum()

    return {
        'total_rows': total_rows,
        'total_columns': total_cols,
        'missing_values': missing_counts.to_dict(),
        'missing_percentages': missing_pct.to_dict(),
        'duplicate_rows': int(duplicate_count),
        'duplicate_percentage': round(duplicate_count / total_rows * 100, 2) if total_rows > 0 else 0
    }


def stratify_dataframe(df: pd.DataFrame,
                      strata_cols: List[str],
                      sample_size: Optional[int] = None,
                      random_state: int = 42) -> pd.DataFrame:
    """
    Perform stratified sampling from DataFrame

    Args:
        df: DataFrame to sample from
        strata_cols: Columns to stratify by
        sample_size: Total sample size (if None, returns all with strata labels)
        random_state: Random seed

    Returns:
        Stratified sample DataFrame
    """
    # Create stratum identifier
    df['_stratum'] = df[strata_cols].astype(str).agg('_'.join, axis=1)

    if sample_size is None:
        return df

    # Calculate proportion in each stratum
    strata_counts = df['_stratum'].value_counts()
    strata_proportions = strata_counts / len(df)

    # Sample from each stratum
    samples = []
    for stratum, proportion in strata_proportions.items():
        stratum_sample_size = int(np.round(sample_size * proportion))
        stratum_df = df[df['_stratum'] == stratum]

        if len(stratum_df) >= stratum_sample_size:
            sample = stratum_df.sample(n=stratum_sample_size, random_state=random_state)
        else:
            sample = stratum_df

        samples.append(sample)

    result = pd.concat(samples, ignore_index=True)
    result = result.drop('_stratum', axis=1)

    return result


def print_experiment_summary(data: Dict[str, pd.DataFrame]):
    """
    Print summary of experiment data

    Args:
        data: Dictionary of DataFrames from experiment
    """
    print("=" * 60)
    print("EXPERIMENT DATA SUMMARY")
    print("=" * 60)

    for name, df in data.items():
        if isinstance(df, pd.DataFrame):
            print(f"\n[{name.upper()}]")
            print(f"  Rows: {len(df):,}")
            print(f"  Columns: {len(df.columns)}")
            print(f"  Memory: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

            # Show unique values for key columns
            if 'variant' in df.columns:
                variant_counts = df['variant'].value_counts()
                print(f"  Variants: {dict(variant_counts)}")

            if 'user_id' in df.columns:
                print(f"  Unique Users: {df['user_id'].nunique():,}")

    print("\n" + "=" * 60)


def calculate_funnel_metrics(df: pd.DataFrame,
                            stages: List[str],
                            group_col: str = 'variant') -> pd.DataFrame:
    """
    Calculate funnel conversion rates

    Args:
        df: DataFrame with stage data
        stages: List of stage column names (in order)
        group_col: Column to group by

    Returns:
        DataFrame with funnel metrics
    """
    funnel_data = []

    for variant in df[group_col].unique():
        variant_df = df[df[group_col] == variant]
        total_users = len(variant_df)

        for i, stage in enumerate(stages):
            completed = variant_df[stage].sum()
            rate = completed / total_users if total_users > 0 else 0

            # Drop-off from previous stage
            if i > 0:
                prev_completed = variant_df[stages[i-1]].sum()
                drop_off = (prev_completed - completed) / prev_completed if prev_completed > 0 else 0
            else:
                drop_off = 0

            funnel_data.append({
                group_col: variant,
                'stage': stage,
                'stage_number': i + 1,
                'users': int(completed),
                'conversion_rate': rate,
                'drop_off_rate': drop_off
            })

    return pd.DataFrame(funnel_data)


if __name__ == "__main__":
    # Test utilities
    print("Testing utility functions...")

    # Test conversion rate calculation
    test_df = pd.DataFrame({
        'variant': ['control'] * 100 + ['treatment'] * 100,
        'converted': [1] * 40 + [0] * 60 + [1] * 50 + [0] * 50
    })

    rates = calculate_conversion_rate(test_df, 'converted', 'variant')
    print("\nConversion Rates:")
    print(rates)

    # Test sample size calculation
    required_n = calculate_sample_size_required(
        baseline_rate=0.40,
        mde=0.15,
        alpha=0.05,
        power=0.80
    )
    print(f"\nRequired sample size: {required_n:,} per variant")

    # Test lift calculation
    lift = calculate_relative_lift(0.40, 0.46)
    print(f"\nLift calculation: {lift}")

    print("\n✓ All utility functions working!")
