"""
Synthetic Data Generator for A/B Testing Platform
Generates realistic user data with ground truth treatment effects
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy import stats
from typing import Tuple, Dict, Optional
import uuid
import logging

from src.config import DataGenerationConfig, ExperimentConfig
from src.experiment_assignment import ExperimentAssignment

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExperimentDataGenerator:
    """Generate realistic synthetic data for dating app experiment"""

    def __init__(self,
                 data_config: DataGenerationConfig,
                 exp_config: ExperimentConfig,
                 seed: int = 42):
        """
        Initialize data generator

        Args:
            data_config: Data generation configuration
            exp_config: Experiment configuration
            seed: Random seed for reproducibility
        """
        self.config = data_config
        self.exp_config = exp_config
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.assigner = ExperimentAssignment()

        logger.info(f"Initialized ExperimentDataGenerator with seed={seed}")

    def generate_users(self) -> pd.DataFrame:
        """
        Generate user demographics with realistic distributions

        Returns:
            DataFrame with user information
        """
        logger.info(f"Generating {self.config.n_users:,} users...")
        n = self.config.n_users

        # Age: Beta distribution with mode around 26
        age_alpha, age_beta = 2, 3
        ages = np.round(
            stats.beta.rvs(age_alpha, age_beta, size=n, random_state=self.seed) *
            (self.config.age_range[1] - self.config.age_range[0]) +
            self.config.age_range[0]
        ).astype(int)

        # Gender distribution (51% Male, 47% Female, 2% Non-binary)
        genders = self.rng.choice(
            ['Male', 'Female', 'Non-binary'],
            size=n,
            p=[0.51, 0.47, 0.02]
        )

        # Locations (weighted by population)
        location_probs = [0.15, 0.13, 0.10, 0.09, 0.08, 0.08, 0.07, 0.07, 0.12, 0.11]
        locations = self.rng.choice(
            self.config.locations,
            size=n,
            p=location_probs
        )

        # Education distribution
        education_choices = list(self.config.education_distribution.keys())
        education_probs = list(self.config.education_distribution.values())
        education = self.rng.choice(education_choices, size=n, p=education_probs)

        # Account type (7% premium)
        account_types = self.rng.choice(
            ['free', 'premium'],
            size=n,
            p=[1 - self.config.premium_rate, self.config.premium_rate]
        )

        # Signup dates (past 6 months, exponentially distributed - more recent users)
        start_date = datetime.strptime(self.exp_config.start_date, '%Y-%m-%d')
        signup_dates = [
            start_date - timedelta(days=int(self.rng.exponential(60)))
            for _ in range(n)
        ]

        users_df = pd.DataFrame({
            'user_id': [str(uuid.uuid4()) for _ in range(n)],
            'signup_date': signup_dates,
            'age': ages,
            'gender': genders,
            'location': locations,
            'education_level': education,
            'account_type': account_types,
            'created_at': datetime.now()
        })

        # Create engagement tier for realistic behavior patterns
        # Will be used for generation but removed from final data
        engagement_probs = list(self.config.engagement_tiers.values())
        users_df['engagement_tier'] = self.rng.choice(
            list(self.config.engagement_tiers.keys()),
            size=n,
            p=engagement_probs
        )

        # Age group for stratification
        users_df['age_group'] = pd.cut(
            users_df['age'],
            bins=self.config.age_bins,
            labels=self.config.age_groups
        )

        logger.info(f"✓ Generated {len(users_df):,} users")
        return users_df

    def generate_pre_metrics(self, users_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate pre-experiment metrics for CUPED with realistic correlations

        Args:
            users_df: User demographics DataFrame

        Returns:
            DataFrame with pre-experiment metrics
        """
        logger.info("Generating pre-experiment metrics for CUPED...")
        n = len(users_df)

        # Engagement multipliers by tier
        tier_multipliers = {
            'power': 3.0,
            'regular': 1.0,
            'casual': 0.3,
            'churned': 0.05
        }

        pre_metrics = []

        for _, user in users_df.iterrows():
            multiplier = tier_multipliers[user['engagement_tier']]

            # Sessions: Gamma distribution
            sessions = max(0, int(self.rng.gamma(2, 3) * multiplier))

            # Matches: correlated with sessions (ρ ≈ 0.65)
            matches = max(0, int(self.rng.negative_binomial(
                max(1, sessions * 0.7), 0.5
            ) * multiplier))

            # Messages: correlated with sessions (ρ ≈ 0.72)
            messages = max(0, int(self.rng.poisson(sessions * 1.2) * multiplier))

            # Time on app: log-normal
            time_minutes = max(0, int(self.rng.lognormal(
                np.log(max(1, sessions * 15)), 0.5
            ) * multiplier))

            # Profile views
            profile_views = max(0, int(self.rng.poisson(sessions * 8) * multiplier))

            pre_metrics.append({
                'user_id': user['user_id'],
                'pre_period_start': datetime.strptime(self.exp_config.start_date, '%Y-%m-%d') - timedelta(days=14),
                'pre_period_end': datetime.strptime(self.exp_config.start_date, '%Y-%m-%d') - timedelta(days=1),
                'pre_sessions_count': sessions,
                'pre_matches_count': matches,
                'pre_messages_sent': messages,
                'pre_total_time_minutes': time_minutes,
                'pre_profile_views': profile_views
            })

        pre_metrics_df = pd.DataFrame(pre_metrics)
        logger.info(f"✓ Generated pre-metrics for {len(pre_metrics_df):,} users")
        return pre_metrics_df

    def generate_experiment_assignments(self, users_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate stratified random assignments

        Args:
            users_df: User demographics DataFrame

        Returns:
            DataFrame with experiment assignments
        """
        logger.info("Generating experiment assignments...")

        assignments = []
        device_types = ['iOS', 'Android']
        app_versions = ['2.5.0', '2.5.1', '2.6.0']

        for _, user in users_df.iterrows():
            # Hash-based assignment for consistency
            variant = self.assigner.assign_variant(
                user['user_id'],
                self.exp_config.experiment_id
            )

            assignments.append({
                'user_id': user['user_id'],
                'experiment_id': self.exp_config.experiment_id,
                'variant': variant,
                'assignment_timestamp': user['signup_date'],
                'device_type': self.rng.choice(device_types, p=[0.55, 0.45]),
                'app_version': self.rng.choice(app_versions, p=[0.2, 0.3, 0.5])
            })

        assignments_df = pd.DataFrame(assignments)

        # Log distribution
        variant_counts = assignments_df['variant'].value_counts()
        logger.info(f"✓ Assignments: Control={variant_counts.get('control', 0):,}, "
                   f"Treatment={variant_counts.get('treatment', 0):,}")

        return assignments_df

    def generate_events(self,
                       users_df: pd.DataFrame,
                       assignments_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate event stream with temporal patterns and treatment effects

        Args:
            users_df: User demographics
            assignments_df: Variant assignments

        Returns:
            DataFrame with events
        """
        logger.info("Generating event stream...")

        start_date = datetime.strptime(self.exp_config.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(self.exp_config.end_date, '%Y-%m-%d')
        duration_days = (end_date - start_date).days

        events = []
        tier_multipliers = {
            'power': 3.0,
            'regular': 1.0,
            'casual': 0.3,
            'churned': 0.05
        }

        # Merge to get variant
        users_with_variant = users_df.merge(
            assignments_df[['user_id', 'variant']],
            on='user_id'
        )

        for _, user in users_with_variant.iterrows():
            multiplier = tier_multipliers[user['engagement_tier']]

            # Apply treatment effect on engagement
            if user['variant'] == 'treatment':
                multiplier *= (1 + self.config.engagement_lift)

            # Number of sessions during experiment
            n_sessions = int(self.rng.poisson(duration_days * multiplier))

            for _ in range(n_sessions):
                # Session timestamp with temporal patterns
                day_offset = self.rng.integers(0, duration_days)
                hour = self._sample_hour_with_peak()  # Peak 6-10pm

                session_time = start_date + timedelta(
                    days=int(day_offset),
                    hours=int(hour),
                    minutes=int(self.rng.integers(0, 60))
                )

                session_id = str(uuid.uuid4())

                # Session duration (seconds)
                duration_seconds = int(self.rng.lognormal(np.log(300), 0.8))

                # Session start event
                events.append({
                    'user_id': user['user_id'],
                    'event_type': 'session_start',
                    'event_timestamp': session_time,
                    'session_id': session_id,
                    'event_properties': {'duration_seconds': duration_seconds},
                    'experiment_id': self.exp_config.experiment_id,
                    'variant': user['variant']
                })

                # Profile views in session
                n_views = self.rng.poisson(8)
                for _ in range(n_views):
                    events.append({
                        'user_id': user['user_id'],
                        'event_type': 'profile_view',
                        'event_timestamp': session_time + timedelta(
                            seconds=int(self.rng.integers(10, max(11, duration_seconds)))
                        ),
                        'session_id': session_id,
                        'event_properties': {},
                        'experiment_id': self.exp_config.experiment_id,
                        'variant': user['variant']
                    })

                # Matches (10% of sessions)
                if self.rng.random() < 0.1 * multiplier:
                    events.append({
                        'user_id': user['user_id'],
                        'event_type': 'match',
                        'event_timestamp': session_time + timedelta(
                            seconds=int(self.rng.integers(10, max(11, duration_seconds)))
                        ),
                        'session_id': session_id,
                        'event_properties': {},
                        'experiment_id': self.exp_config.experiment_id,
                        'variant': user['variant']
                    })

                # Messages (5% of sessions)
                if self.rng.random() < 0.05 * multiplier:
                    n_messages = self.rng.poisson(2)
                    for _ in range(n_messages):
                        events.append({
                            'user_id': user['user_id'],
                            'event_type': 'message_sent',
                            'event_timestamp': session_time + timedelta(
                                seconds=int(self.rng.integers(10, max(11, duration_seconds)))
                            ),
                            'session_id': session_id,
                            'event_properties': {},
                            'experiment_id': self.exp_config.experiment_id,
                            'variant': user['variant']
                        })

        events_df = pd.DataFrame(events)
        logger.info(f"✓ Generated {len(events_df):,} events")
        return events_df

    def generate_verification_flow(self,
                                   users_df: pd.DataFrame,
                                   assignments_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Generate verification attempts with treatment effects

        Args:
            users_df: User demographics
            assignments_df: Variant assignments

        Returns:
            Tuple of (verification_attempts, verification_status) DataFrames
        """
        logger.info("Generating verification flow...")

        verification_attempts = []
        verification_status = []

        start_date = datetime.strptime(self.exp_config.start_date, '%Y-%m-%d')

        # Merge to get variant
        users_with_variant = users_df.merge(
            assignments_df[['user_id', 'variant']],
            on='user_id'
        )

        for _, user in users_with_variant.iterrows():
            # Tier 1: Email verification
            if self.rng.random() < self.config.tier1_start_rate:
                # Apply treatment effect
                # Device type affects conversion (iOS converts 1.3x Android)
                device_multiplier = 1.3 if user.get("device_type") == "iOS" else 1.0
                
                completion_rate = self.config.tier1_completion_rate * device_multiplier
                if user['variant'] == 'treatment':
                    completion_rate *= (1 + self.config.tier1_lift)

                attempt_time = start_date + timedelta(
                    days=int(self.rng.integers(0, 3)),
                    hours=int(self.rng.integers(0, 24))
                )

                # Did user complete?
                tier1_completed = self.rng.random() < completion_rate

                if tier1_completed:
                    time_to_complete = int(self.rng.lognormal(np.log(120), 0.3))
                    completion_status = 'completed'
                    completion_time = attempt_time + timedelta(seconds=time_to_complete)
                    failure_reason = None
                else:
                    time_to_complete = int(self.rng.lognormal(np.log(60), 0.5))
                    completion_status = self.rng.choice(['abandoned', 'failed'], p=[0.7, 0.3])
                    completion_time = None
                    failure_reason = 'user_abandoned' if completion_status == 'abandoned' else 'verification_failed'

                verification_attempts.append({
                    'user_id': user['user_id'],
                    'verification_tier': 1,
                    'attempt_timestamp': attempt_time,
                    'completion_status': completion_status,
                    'completion_timestamp': completion_time,
                    'time_to_complete_seconds': time_to_complete if tier1_completed else None,
                    'failure_reason': failure_reason,
                    'experiment_id': self.exp_config.experiment_id,
                    'variant': user['variant']
                })

                # Tier 2: Badge/ID verification (conditional on Tier 1 completion)
                if tier1_completed and self.rng.random() < self.config.tier2_start_rate:
                    # Apply treatment effect
                    tier2_completion_rate = self.config.tier2_completion_rate
                    if user['variant'] == 'treatment':
                        tier2_completion_rate *= (1 + self.config.tier2_lift)

                    tier2_attempt_time = completion_time + timedelta(
                        hours=int(self.rng.integers(1, 48))
                    )
                    tier2_completed = self.rng.random() < tier2_completion_rate

                    if tier2_completed:
                        time_to_complete = int(self.rng.lognormal(np.log(180), 0.4))
                        completion_status = 'completed'
                        tier2_completion_time = tier2_attempt_time + timedelta(seconds=time_to_complete)
                        failure_reason = None
                    else:
                        time_to_complete = int(self.rng.lognormal(np.log(90), 0.5))
                        completion_status = self.rng.choice(['abandoned', 'failed'], p=[0.6, 0.4])
                        tier2_completion_time = None
                        failure_reason = 'user_abandoned' if completion_status == 'abandoned' else 'verification_failed'

                    verification_attempts.append({
                        'user_id': user['user_id'],
                        'verification_tier': 2,
                        'attempt_timestamp': tier2_attempt_time,
                        'completion_status': completion_status,
                        'completion_timestamp': tier2_completion_time,
                        'time_to_complete_seconds': time_to_complete if tier2_completed else None,
                        'failure_reason': failure_reason,
                        'experiment_id': self.exp_config.experiment_id,
                        'variant': user['variant']
                    })

                    # Verification status
                    verification_status.append({
                        'user_id': user['user_id'],
                        'tier1_verified': True,
                        'tier1_verification_date': completion_time,
                        'tier1_domain': f"{user['education_level'].lower().replace(' ', '')}.edu",
                        'tier2_verified': tier2_completed,
                        'tier2_verification_date': tier2_completion_time if tier2_completed else None,
                        'verification_badge_type': 'university' if tier2_completed else None,
                        'last_updated': datetime.now()
                    })
                else:
                    # Only Tier 1 verified (or attempted)
                    if tier1_completed:
                        verification_status.append({
                            'user_id': user['user_id'],
                            'tier1_verified': True,
                            'tier1_verification_date': completion_time,
                            'tier1_domain': f"{user['education_level'].lower().replace(' ', '')}.edu",
                            'tier2_verified': False,
                            'tier2_verification_date': None,
                            'verification_badge_type': None,
                            'last_updated': datetime.now()
                        })

        attempts_df = pd.DataFrame(verification_attempts)
        status_df = pd.DataFrame(verification_status)

        logger.info(f"✓ Generated {len(attempts_df):,} verification attempts")
        logger.info(f"✓ Generated {len(status_df):,} verification statuses")

        return attempts_df, status_df

    def _sample_hour_with_peak(self) -> int:
        """Sample hour of day with peak usage 6-10pm"""
        # Peak hours (18-22): 40% of traffic
        # Other hours: 60% of traffic
        if self.rng.random() < 0.4:
            return self.rng.integers(18, 23)
        else:
            return self.rng.integers(0, 18)

    def validate_data_quality(self,
                             users_df: pd.DataFrame,
                             assignments_df: pd.DataFrame,
                             pre_metrics_df: pd.DataFrame,
                             verification_df: pd.DataFrame) -> Dict:
        """
        Comprehensive data quality validation

        Args:
            users_df: Users DataFrame
            assignments_df: Assignments DataFrame
            pre_metrics_df: Pre-metrics DataFrame
            verification_df: Verification attempts DataFrame

        Returns:
            Dictionary with validation results
        """
        logger.info("Validating data quality...")
        validation_results = {}

        # 1. Sample Ratio Mismatch check
        variant_counts = assignments_df['variant'].value_counts()
        control_count = variant_counts.get('control', 0)
        treatment_count = variant_counts.get('treatment', 0)
        total = control_count + treatment_count

        expected_control = total * 0.5
        chi2_stat = ((control_count - expected_control)**2 / expected_control +
                     (treatment_count - expected_control)**2 / expected_control)

        from scipy.stats import chi2
        p_value = 1 - chi2.cdf(chi2_stat, df=1)

        validation_results['srm_check'] = {
            'passed': p_value > 0.01,
            'p_value': p_value,
            'control_count': int(control_count),
            'treatment_count': int(treatment_count),
            'observed_ratio': control_count / total if total > 0 else 0
        }

        # 2. Covariate balance (t-tests on pre-metrics)
        merged = assignments_df.merge(pre_metrics_df, on='user_id')
        control_pre = merged[merged['variant'] == 'control']
        treatment_pre = merged[merged['variant'] == 'treatment']

        from scipy.stats import ttest_ind

        covariate_balance = {}
        for col in ['pre_sessions_count', 'pre_matches_count', 'pre_messages_sent']:
            if col in control_pre.columns and col in treatment_pre.columns:
                t_stat, p_val = ttest_ind(
                    control_pre[col].dropna(),
                    treatment_pre[col].dropna()
                )
                covariate_balance[col] = {
                    'p_value': p_val,
                    'balanced': p_val > 0.05
                }

        validation_results['covariate_balance'] = covariate_balance

        # 3. Treatment effect validation (ground truth check)
        tier1_data = verification_df[verification_df['verification_tier'] == 1].copy()
        tier1_data['completed'] = (tier1_data['completion_status'] == 'completed').astype(int)

        control_rate = tier1_data[tier1_data['variant'] == 'control']['completed'].mean()
        treatment_rate = tier1_data[tier1_data['variant'] == 'treatment']['completed'].mean()
        observed_lift = (treatment_rate - control_rate) / control_rate if control_rate > 0 else 0

        validation_results['treatment_effect'] = {
            'control_rate': control_rate,
            'treatment_rate': treatment_rate,
            'observed_lift': observed_lift,
            'expected_lift': self.config.tier1_lift,
            'lift_close_to_expected': abs(observed_lift - self.config.tier1_lift) < 0.03
        }

        return validation_results

    def generate_all_data(self) -> Dict[str, pd.DataFrame]:
        """
        Generate complete synthetic dataset

        Returns:
            Dictionary of DataFrames with all generated data
        """
        logger.info("=" * 60)
        logger.info("GENERATING COMPLETE SYNTHETIC DATASET")
        logger.info("=" * 60)

        # Generate all data
        users_df = self.generate_users()
        pre_metrics_df = self.generate_pre_metrics(users_df)
        assignments_df = self.generate_experiment_assignments(users_df)
        events_df = self.generate_events(users_df, assignments_df)
        verification_attempts_df, verification_status_df = self.generate_verification_flow(
            users_df, assignments_df
        )

        # Validate data quality
        validation_results = self.validate_data_quality(
            users_df, assignments_df, pre_metrics_df, verification_attempts_df
        )

        # Print validation results
        logger.info("\n" + "=" * 60)
        logger.info("DATA QUALITY VALIDATION RESULTS")
        logger.info("=" * 60)

        logger.info(f"\n[SRM Check]")
        srm = validation_results['srm_check']
        logger.info(f"  Status: {'PASSED ✓' if srm['passed'] else 'FAILED ✗'}")
        logger.info(f"  Control: {srm['control_count']:,}")
        logger.info(f"  Treatment: {srm['treatment_count']:,}")
        logger.info(f"  p-value: {srm['p_value']:.4f}")

        logger.info(f"\n[Covariate Balance]")
        for metric, result in validation_results['covariate_balance'].items():
            status = 'BALANCED ✓' if result['balanced'] else 'IMBALANCED ✗'
            logger.info(f"  {metric}: {status} (p={result['p_value']:.4f})")

        logger.info(f"\n[Treatment Effect Validation]")
        te = validation_results['treatment_effect']
        logger.info(f"  Control Rate: {te['control_rate']:.2%}")
        logger.info(f"  Treatment Rate: {te['treatment_rate']:.2%}")
        logger.info(f"  Observed Lift: {te['observed_lift']:.2%}")
        logger.info(f"  Expected Lift: {te['expected_lift']:.2%}")
        logger.info(f"  Match: {'YES ✓' if te['lift_close_to_expected'] else 'NO ✗'}")

        logger.info("\n" + "=" * 60)

        # Remove temporary columns
        users_df = users_df.drop(['engagement_tier', 'age_group'], axis=1)

        return {
            'users': users_df,
            'pre_metrics': pre_metrics_df,
            'assignments': assignments_df,
            'events': events_df,
            'verification_attempts': verification_attempts_df,
            'verification_status': verification_status_df,
            'validation': validation_results
        }


if __name__ == "__main__":
    # Generate synthetic data
    from src.config import DATA_CONFIG, EXP_CONFIG

    generator = ExperimentDataGenerator(DATA_CONFIG, EXP_CONFIG)
    data = generator.generate_all_data()

    # Save to CSV files
    logger.info("\nSaving data to CSV files...")
    data['users'].to_csv('data/users.csv', index=False)
    data['pre_metrics'].to_csv('data/user_pre_metrics.csv', index=False)
    data['assignments'].to_csv('data/experiment_assignments.csv', index=False)
    data['events'].to_csv('data/events.csv', index=False)
    data['verification_attempts'].to_csv('data/verification_attempts.csv', index=False)
    data['verification_status'].to_csv('data/verification_status.csv', index=False)

    logger.info("\n✓ All data generated and saved successfully!")
    logger.info(f"  Users: {len(data['users']):,}")
    logger.info(f"  Events: {len(data['events']):,}")
    logger.info(f"  Verification Attempts: {len(data['verification_attempts']):,}")
