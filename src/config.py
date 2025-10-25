"""
Configuration management for WorkHeart A/B Testing Platform
"""
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class DatabaseConfig:
    """Supabase database configuration"""
    url: str
    key: str

    @classmethod
    def from_env(cls):
        """Load configuration from environment variables"""
        return cls(
            url=os.getenv('SUPABASE_URL', ''),
            key=os.getenv('SUPABASE_KEY', '')
        )

    def is_configured(self) -> bool:
        """Check if database credentials are configured"""
        return bool(self.url and self.key)


@dataclass
class ExperimentConfig:
    """Experiment configuration and parameters"""
    experiment_id: str = 'verification_v1'
    experiment_name: str = 'Two-Tier Verification Optimization'
    start_date: str = '2024-07-01'
    end_date: str = '2024-07-14'
    alpha: float = 0.05
    power: float = 0.80
    mde: float = 0.15  # 15% minimum detectable effect

    def to_dict(self) -> Dict:
        """Convert to dictionary for database insertion"""
        return {
            'experiment_id': self.experiment_id,
            'experiment_name': self.experiment_name,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'minimum_detectable_effect': self.mde,
            'alpha': self.alpha,
            'power': self.power,
            'status': 'active',
            'description': 'Testing optimized two-tier verification flow (email + badge/ID)',
            'hypothesis': 'Streamlined UX will increase verification completion rates',
            'target_metric': 'tier1_completion_rate'
        }


@dataclass
class DataGenerationConfig:
    """Synthetic data generation parameters"""
    n_users: int = 50000
    n_months: int = 6
    dau_range: tuple = (1000, 2000)

    # User demographics
    age_range: tuple = (18, 60)
    locations: List[str] = field(default_factory=lambda: [
        'New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix',
        'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'Austin'
    ])
    education_distribution: Dict[str, float] = field(default_factory=lambda: {
        'Bachelors': 0.225,
        'Masters': 0.45,
        'PhD': 0.135,
        'Other': 0.10
    })
    premium_rate: float = 0.07

    # Retention rates
    retention_d1: float = 0.20
    retention_d7: float = 0.08
    retention_d30: float = 0.03

    # Verification baseline rates
    tier1_start_rate: float = 0.75
    tier1_completion_rate: float = 0.40
    tier2_start_rate: float = 0.80
    tier2_completion_rate: float = 0.25

    # Treatment effects (ground truth for synthetic data)
    tier1_lift: float = 0.15  # 15% relative improvement
    tier2_lift: float = 0.20  # 20% relative improvement
    engagement_lift: float = 0.12  # 12% sessions lift

    # Engagement tier distribution
    engagement_tiers: Dict[str, float] = field(default_factory=lambda: {
        'power': 0.10,
        'regular': 0.60,
        'casual': 0.20,
        'churned': 0.10
    })

    # Age group bins
    age_groups: List[str] = field(default_factory=lambda: ['18-24', '25-34', '35+'])
    age_bins: List[int] = field(default_factory=lambda: [18, 25, 35, 60])


@dataclass
class AnalysisConfig:
    """Statistical analysis configuration"""
    alpha: float = 0.05
    power: float = 0.80
    use_cuped: bool = True
    multiple_testing_method: str = 'fdr_bh'  # Benjamini-Hochberg
    srm_threshold: float = 0.01
    min_sample_size: int = 1000

    # Metrics to analyze
    primary_metric: str = 'tier1_completion_rate'
    secondary_metrics: List[str] = field(default_factory=lambda: [
        'tier2_completion_rate',
        'sessions_count',
        'time_to_complete_tier1',
        'time_to_complete_tier2'
    ])

    # CUPED covariate mapping
    cuped_covariates: Dict[str, str] = field(default_factory=lambda: {
        'sessions_count': 'pre_sessions_count',
        'matches_count': 'pre_matches_count',
        'messages_sent': 'pre_messages_sent'
    })


@dataclass
class DashboardConfig:
    """Dashboard configuration"""
    title: str = "WorkHeart Verification A/B Test Dashboard"
    page_icon: str = "💙"
    layout: str = "wide"
    refresh_interval: int = 300  # seconds

    # Chart colors
    control_color: str = 'lightblue'
    treatment_color: str = 'lightgreen'

    # Confidence interval
    ci_level: float = 0.95


# Global configuration instances
DB_CONFIG = DatabaseConfig.from_env()
EXP_CONFIG = ExperimentConfig()
DATA_CONFIG = DataGenerationConfig()
ANALYSIS_CONFIG = AnalysisConfig()
DASHBOARD_CONFIG = DashboardConfig()


def validate_config() -> Dict[str, bool]:
    """Validate all configurations"""
    validations = {
        'database': DB_CONFIG.is_configured(),
        'experiment': bool(EXP_CONFIG.experiment_id),
        'data_generation': DATA_CONFIG.n_users > 0,
        'analysis': 0 < ANALYSIS_CONFIG.alpha < 1,
        'dashboard': bool(DASHBOARD_CONFIG.title)
    }
    return validations


def print_config_summary():
    """Print configuration summary for debugging"""
    print("=" * 60)
    print("WORKHEART A/B TESTING PLATFORM - CONFIGURATION SUMMARY")
    print("=" * 60)
    print(f"\n[Database]")
    print(f"  Configured: {DB_CONFIG.is_configured()}")
    print(f"\n[Experiment]")
    print(f"  ID: {EXP_CONFIG.experiment_id}")
    print(f"  Name: {EXP_CONFIG.experiment_name}")
    print(f"  Duration: {EXP_CONFIG.start_date} to {EXP_CONFIG.end_date}")
    print(f"  MDE: {EXP_CONFIG.mde:.1%}")
    print(f"  Alpha: {EXP_CONFIG.alpha}")
    print(f"  Power: {EXP_CONFIG.power}")
    print(f"\n[Data Generation]")
    print(f"  Users: {DATA_CONFIG.n_users:,}")
    print(f"  Tier 1 Baseline: {DATA_CONFIG.tier1_completion_rate:.1%}")
    print(f"  Tier 2 Baseline: {DATA_CONFIG.tier2_completion_rate:.1%}")
    print(f"  Treatment Lift (T1): {DATA_CONFIG.tier1_lift:.1%}")
    print(f"  Treatment Lift (T2): {DATA_CONFIG.tier2_lift:.1%}")
    print(f"\n[Analysis]")
    print(f"  Primary Metric: {ANALYSIS_CONFIG.primary_metric}")
    print(f"  Secondary Metrics: {len(ANALYSIS_CONFIG.secondary_metrics)}")
    print(f"  Use CUPED: {ANALYSIS_CONFIG.use_cuped}")
    print(f"  Multiple Testing: {ANALYSIS_CONFIG.multiple_testing_method}")
    print("=" * 60)


if __name__ == "__main__":
    # Test configuration
    print_config_summary()
    validations = validate_config()
    print(f"\nValidation Results: {validations}")
