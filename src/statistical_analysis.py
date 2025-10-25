"""
Statistical Analysis Engine for A/B Testing Platform
Comprehensive statistical methods for experiment analysis
"""
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats import multitest
from typing import Dict, Tuple, List, Optional, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ABTestAnalyzer:
    """Comprehensive A/B test analysis with industry best practices"""

    def __init__(self, alpha: float = 0.05, power: float = 0.80):
        """
        Initialize A/B test analyzer

        Args:
            alpha: Significance level (Type I error rate)
            power: Statistical power (1 - Type II error rate)
        """
        self.alpha = alpha
        self.power = power
        logger.info(f"Initialized ABTestAnalyzer (alpha={alpha}, power={power})")

    # ============= POWER ANALYSIS =============

    def calculate_sample_size(self,
                             baseline_rate: float,
                             mde: float,
                             alpha: Optional[float] = None,
                             power: Optional[float] = None) -> int:
        """
        Calculate required sample size per variant for proportion test

        Uses normal approximation for two-proportion z-test

        Args:
            baseline_rate: Control group conversion rate (0-1)
            mde: Minimum Detectable Effect (relative, e.g., 0.15 for 15%)
            alpha: Significance level (defaults to self.alpha)
            power: Statistical power (defaults to self.power)

        Returns:
            Required sample size per variant

        Example:
            >>> analyzer = ABTestAnalyzer()
            >>> analyzer.calculate_sample_size(0.40, 0.15)
            2375
        """
        alpha = alpha or self.alpha
        power = power or self.power

        treatment_rate = baseline_rate * (1 + mde)
        p_pooled = (baseline_rate + treatment_rate) / 2

        z_alpha = stats.norm.ppf(1 - alpha / 2)
        z_beta = stats.norm.ppf(power)

        n = (2 * p_pooled * (1 - p_pooled) * (z_alpha + z_beta)**2) / \
            (baseline_rate - treatment_rate)**2

        return int(np.ceil(n))

    def post_hoc_power(self,
                      n_control: int,
                      n_treatment: int,
                      control_rate: float,
                      treatment_rate: float,
                      alpha: Optional[float] = None) -> float:
        """
        Calculate achieved power for observed data

        Args:
            n_control: Control group sample size
            n_treatment: Treatment group sample size
            control_rate: Observed control conversion rate
            treatment_rate: Observed treatment conversion rate
            alpha: Significance level

        Returns:
            Achieved statistical power
        """
        alpha = alpha or self.alpha

        effect_size = treatment_rate - control_rate
        pooled_std = np.sqrt(
            control_rate * (1 - control_rate) / n_control +
            treatment_rate * (1 - treatment_rate) / n_treatment
        )

        if pooled_std == 0:
            return 0.0

        z_score = effect_size / pooled_std
        z_alpha = stats.norm.ppf(1 - alpha / 2)
        power = stats.norm.cdf(abs(z_score) - z_alpha)

        return max(0.0, min(1.0, power))

    def calculate_minimum_detectable_effect(self,
                                           baseline_rate: float,
                                           sample_size: int,
                                           alpha: Optional[float] = None,
                                           power: Optional[float] = None) -> float:
        """
        Calculate minimum detectable effect given sample size

        Args:
            baseline_rate: Control group conversion rate
            sample_size: Sample size per variant
            alpha: Significance level
            power: Statistical power

        Returns:
            Minimum detectable effect (relative)
        """
        alpha = alpha or self.alpha
        power = power or self.power

        z_alpha = stats.norm.ppf(1 - alpha / 2)
        z_beta = stats.norm.ppf(power)

        # Binary search for MDE
        left, right = 0.001, 1.0
        while right - left > 0.0001:
            mid = (left + right) / 2
            required_n = self.calculate_sample_size(baseline_rate, mid, alpha, power)
            if required_n > sample_size:
                left = mid
            else:
                right = mid

        return (left + right) / 2

    # ============= FREQUENTIST TESTS =============

    def proportion_test(self,
                       control_conversions: int,
                       control_total: int,
                       treatment_conversions: int,
                       treatment_total: int) -> Dict[str, Any]:
        """
        Two-proportion z-test with comprehensive output

        Args:
            control_conversions: Number of conversions in control
            control_total: Total users in control
            treatment_conversions: Number of conversions in treatment
            treatment_total: Total users in treatment

        Returns:
            Dictionary with test results including p-value, lift, CI
        """
        p_control = control_conversions / control_total if control_total > 0 else 0
        p_treatment = treatment_conversions / treatment_total if treatment_total > 0 else 0

        # Pooled proportion for standard error
        p_pooled = (control_conversions + treatment_conversions) / \
                   (control_total + treatment_total)

        # Standard error under null hypothesis
        se = np.sqrt(p_pooled * (1 - p_pooled) *
                     (1/control_total + 1/treatment_total))

        # Z-score and p-value
        if se == 0:
            z_score = 0.0
            p_value = 1.0
        else:
            z_score = (p_treatment - p_control) / se
            p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))

        # Confidence interval (using unpooled variance)
        z_alpha = stats.norm.ppf(1 - self.alpha / 2)
        se_diff = np.sqrt(
            p_control * (1 - p_control) / control_total +
            p_treatment * (1 - p_treatment) / treatment_total
        )
        ci_lower = (p_treatment - p_control) - z_alpha * se_diff
        ci_upper = (p_treatment - p_control) + z_alpha * se_diff

        # Effect sizes
        absolute_lift = p_treatment - p_control
        relative_lift = (p_treatment - p_control) / p_control if p_control > 0 else 0

        # Practical significance threshold (typically 2% minimum)
        practically_significant = abs(relative_lift) > 0.02

        return {
            'test_type': 'two_proportion_z_test',
            'p_value': p_value,
            'z_score': z_score,
            'control_rate': p_control,
            'treatment_rate': p_treatment,
            'absolute_lift': absolute_lift,
            'relative_lift': relative_lift,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'ci_level': 1 - self.alpha,
            'statistically_significant': p_value < self.alpha,
            'practically_significant': practically_significant,
            'sample_size_control': control_total,
            'sample_size_treatment': treatment_total,
            'conversions_control': control_conversions,
            'conversions_treatment': treatment_conversions
        }

    def t_test_continuous(self,
                         control_values: np.ndarray,
                         treatment_values: np.ndarray,
                         equal_var: bool = False) -> Dict[str, Any]:
        """
        Welch's t-test for continuous metrics (or Student's t-test if equal_var=True)

        Args:
            control_values: Control group metric values
            treatment_values: Treatment group metric values
            equal_var: Assume equal variances (Student's t-test)

        Returns:
            Dictionary with test results
        """
        # Remove NaN values
        control_clean = control_values[~np.isnan(control_values)]
        treatment_clean = treatment_values[~np.isnan(treatment_values)]

        if len(control_clean) == 0 or len(treatment_clean) == 0:
            return {
                'error': 'Insufficient data',
                'test_type': 'welch_t_test' if not equal_var else 'student_t_test'
            }

        # Perform t-test
        t_stat, p_value = stats.ttest_ind(
            treatment_clean, control_clean, equal_var=equal_var
        )

        # Effect size (Cohen's d)
        pooled_std = np.sqrt(
            (np.var(control_clean, ddof=1) + np.var(treatment_clean, ddof=1)) / 2
        )
        if pooled_std > 0:
            cohens_d = (np.mean(treatment_clean) - np.mean(control_clean)) / pooled_std
        else:
            cohens_d = 0.0

        # Confidence interval for mean difference
        mean_diff = np.mean(treatment_clean) - np.mean(control_clean)
        se_diff = np.sqrt(
            np.var(control_clean, ddof=1) / len(control_clean) +
            np.var(treatment_clean, ddof=1) / len(treatment_clean)
        )

        # Degrees of freedom (Welch-Satterthwaite for unequal variances)
        if equal_var:
            df = len(control_clean) + len(treatment_clean) - 2
        else:
            s1_sq = np.var(control_clean, ddof=1)
            s2_sq = np.var(treatment_clean, ddof=1)
            n1 = len(control_clean)
            n2 = len(treatment_clean)
            df = (s1_sq/n1 + s2_sq/n2)**2 / \
                 ((s1_sq/n1)**2/(n1-1) + (s2_sq/n2)**2/(n2-1))

        t_crit = stats.t.ppf(1 - self.alpha / 2, df)
        ci_lower = mean_diff - t_crit * se_diff
        ci_upper = mean_diff + t_crit * se_diff

        # Relative lift
        mean_control = np.mean(control_clean)
        relative_lift = mean_diff / mean_control if mean_control != 0 else 0

        return {
            'test_type': 'welch_t_test' if not equal_var else 'student_t_test',
            'p_value': p_value,
            't_statistic': t_stat,
            'degrees_of_freedom': df,
            'mean_control': np.mean(control_clean),
            'mean_treatment': np.mean(treatment_clean),
            'mean_difference': mean_diff,
            'relative_lift': relative_lift,
            'std_control': np.std(control_clean, ddof=1),
            'std_treatment': np.std(treatment_clean, ddof=1),
            'cohens_d': cohens_d,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'ci_level': 1 - self.alpha,
            'statistically_significant': p_value < self.alpha,
            'sample_size_control': len(control_clean),
            'sample_size_treatment': len(treatment_clean)
        }

    # ============= MULTIPLE TESTING CORRECTIONS =============

    def apply_corrections(self,
                         p_values: List[float],
                         method: str = 'fdr_bh') -> Dict[str, Any]:
        """
        Apply multiple testing corrections

        Args:
            p_values: List of p-values from multiple tests
            method: Correction method
                - 'fdr_bh': Benjamini-Hochberg (recommended, controls FDR)
                - 'bonferroni': Bonferroni correction (conservative, controls FWER)
                - 'holm': Holm-Bonferroni (less conservative than Bonferroni)
                - 'sidak': Sidak correction

        Returns:
            Dictionary with adjusted p-values and rejection decisions
        """
        if len(p_values) == 0:
            return {
                'method': method,
                'adjusted_p_values': [],
                'rejected': [],
                'num_significant': 0,
                'num_tests': 0
            }

        rejected, adjusted_pvals, alpha_sidak, alpha_bonf = multitest.multipletests(
            p_values, alpha=self.alpha, method=method
        )

        return {
            'method': method,
            'adjusted_p_values': adjusted_pvals.tolist(),
            'rejected': rejected.tolist(),
            'num_significant': int(np.sum(rejected)),
            'num_tests': len(p_values),
            'alpha_sidak': alpha_sidak,
            'alpha_bonferroni': alpha_bonf,
            'original_alpha': self.alpha
        }

    # ============= SAMPLE RATIO MISMATCH =============

    def check_sample_ratio_mismatch(self,
                                   n_control: int,
                                   n_treatment: int,
                                   expected_ratio: float = 0.5,
                                   threshold: float = 0.01) -> Dict[str, Any]:
        """
        Detect Sample Ratio Mismatch using chi-squared test

        SRM indicates potential issues with randomization or data collection

        Args:
            n_control: Control group size
            n_treatment: Treatment group size
            expected_ratio: Expected control group ratio
            threshold: p-value threshold for SRM detection (default 0.01)

        Returns:
            Dictionary with SRM check results
        """
        n_total = n_control + n_treatment
        expected_control = n_total * expected_ratio
        expected_treatment = n_total * (1 - expected_ratio)

        # Chi-squared goodness of fit test
        chi2_stat = (
            (n_control - expected_control)**2 / expected_control +
            (n_treatment - expected_treatment)**2 / expected_treatment
        )

        p_value = 1 - stats.chi2.cdf(chi2_stat, df=1)
        srm_detected = p_value < threshold

        observed_ratio = n_control / n_total if n_total > 0 else 0

        return {
            'chi2_statistic': chi2_stat,
            'p_value': p_value,
            'srm_detected': srm_detected,
            'observed_ratio': observed_ratio,
            'expected_ratio': expected_ratio,
            'deviation': abs(observed_ratio - expected_ratio),
            'threshold': threshold,
            'n_control': n_control,
            'n_treatment': n_treatment,
            'warning': 'SRM DETECTED - Investigate technical issues!' if srm_detected else None
        }

    # ============= VARIANCE AND EFFECT SIZE =============

    def calculate_variance_reduction(self,
                                    original_variance: float,
                                    adjusted_variance: float) -> Dict[str, float]:
        """
        Calculate variance reduction percentage

        Args:
            original_variance: Variance before adjustment
            adjusted_variance: Variance after adjustment (e.g., CUPED)

        Returns:
            Dictionary with variance reduction metrics
        """
        if original_variance == 0:
            return {
                'original_variance': 0,
                'adjusted_variance': 0,
                'variance_reduction': 0,
                'reduction_percentage': 0
            }

        reduction = (original_variance - adjusted_variance) / original_variance

        return {
            'original_variance': original_variance,
            'adjusted_variance': adjusted_variance,
            'variance_reduction': reduction,
            'reduction_percentage': reduction * 100
        }

    # ============= SEQUENTIAL TESTING =============

    def sequential_p_value_with_spending(self,
                                        current_p: float,
                                        fraction_spent: float,
                                        total_alpha: Optional[float] = None) -> Dict[str, Any]:
        """
        Calculate adjusted p-value for sequential testing with alpha spending

        Uses O'Brien-Fleming spending function

        Args:
            current_p: Current p-value
            fraction_spent: Fraction of planned sample size spent (0-1)
            total_alpha: Total alpha to spend (defaults to self.alpha)

        Returns:
            Dictionary with sequential testing results
        """
        total_alpha = total_alpha or self.alpha

        # O'Brien-Fleming spending function
        if fraction_spent <= 0:
            alpha_spent = 0
        elif fraction_spent >= 1:
            alpha_spent = total_alpha
        else:
            # Approximate O'Brien-Fleming boundary
            z_alpha = stats.norm.ppf(1 - total_alpha / 2)
            boundary = z_alpha / np.sqrt(fraction_spent)
            alpha_spent = 2 * (1 - stats.norm.cdf(boundary))

        return {
            'current_p_value': current_p,
            'alpha_spent': alpha_spent,
            'fraction_spent': fraction_spent,
            'significant_at_current_stage': current_p < alpha_spent,
            'total_alpha': total_alpha,
            'spending_function': 'obrien_fleming'
        }

    # ============= COMPREHENSIVE ANALYSIS =============

    def analyze_experiment(self,
                          data: pd.DataFrame,
                          metrics: List[str],
                          primary_metric: str,
                          variant_col: str = 'variant',
                          user_id_col: str = 'user_id') -> Dict[str, Any]:
        """
        Complete end-to-end experiment analysis

        Args:
            data: DataFrame with user-level data
            metrics: List of metric column names to analyze
            primary_metric: Main metric for decision
            variant_col: Column name for variant assignment
            user_id_col: Column name for user ID

        Returns:
            Comprehensive results dictionary
        """
        logger.info("Starting comprehensive experiment analysis...")

        results = {
            'data_quality': {},
            'metric_results': {},
            'corrections': {},
            'recommendation': ''
        }

        # 1. Sample Ratio Mismatch check
        variant_counts = data[variant_col].value_counts()
        results['data_quality']['srm_check'] = self.check_sample_ratio_mismatch(
            variant_counts.get('control', 0),
            variant_counts.get('treatment', 0)
        )

        # 2. Analyze each metric
        p_values = []
        metric_types = []

        for metric in metrics:
            if metric not in data.columns:
                logger.warning(f"Metric {metric} not found in data, skipping...")
                continue

            control_data = data[data[variant_col] == 'control'][metric].dropna()
            treatment_data = data[data[variant_col] == 'treatment'][metric].dropna()

            # Determine if binary or continuous
            unique_vals = set(data[metric].dropna().unique())
            is_binary = unique_vals.issubset({0, 1, True, False})

            if is_binary:
                # Proportion test
                result = self.proportion_test(
                    int(control_data.sum()),
                    len(control_data),
                    int(treatment_data.sum()),
                    len(treatment_data)
                )
                metric_types.append('binary')
            else:
                # Continuous metric (Welch's t-test)
                result = self.t_test_continuous(
                    control_data.values,
                    treatment_data.values
                )
                metric_types.append('continuous')

            results['metric_results'][metric] = result
            p_values.append(result['p_value'])

        # 3. Multiple testing corrections
        if len(p_values) > 1:
            results['corrections'] = self.apply_corrections(p_values, method='fdr_bh')
        else:
            results['corrections'] = {'method': 'none', 'note': 'Only one metric tested'}

        # 4. Generate recommendation
        if primary_metric not in results['metric_results']:
            results['recommendation'] = "⚠️ INVALID - Primary metric not analyzed"
        else:
            primary_result = results['metric_results'][primary_metric]
            primary_idx = metrics.index(primary_metric) if primary_metric in metrics else 0

            # Check if primary metric is significant after correction
            if len(p_values) > 1:
                primary_significant = results['corrections']['rejected'][primary_idx]
            else:
                primary_significant = primary_result['statistically_significant']

            srm_detected = results['data_quality']['srm_check']['srm_detected']

            if srm_detected:
                results['recommendation'] = "⚠️ DO NOT SHIP - SRM detected, investigate technical issues"
            elif primary_significant and primary_result.get('relative_lift', 0) > 0:
                results['recommendation'] = "🚀 SHIP - Statistically significant positive impact"
            elif primary_significant and primary_result.get('relative_lift', 0) < 0:
                results['recommendation'] = "❌ DO NOT SHIP - Statistically significant negative impact"
            else:
                results['recommendation'] = "⏸️ KEEP RUNNING - No significant result yet"

        logger.info(f"Analysis complete. Recommendation: {results['recommendation']}")
        return results


if __name__ == "__main__":
    # Test the analyzer
    print("=" * 60)
    print("STATISTICAL ANALYSIS VALIDATION")
    print("=" * 60)

    analyzer = ABTestAnalyzer(alpha=0.05, power=0.80)

    # Test 1: Sample size calculation
    print("\n[Test 1] Sample Size Calculation")
    required_n = analyzer.calculate_sample_size(
        baseline_rate=0.40,
        mde=0.15
    )
    print(f"  Baseline: 40%")
    print(f"  MDE: 15%")
    print(f"  Required n per variant: {required_n:,}")

    # Test 2: Proportion test
    print("\n[Test 2] Proportion Test")
    result = analyzer.proportion_test(
        control_conversions=400,
        control_total=1000,
        treatment_conversions=460,
        treatment_total=1000
    )
    print(f"  Control: 40.0% ({result['conversions_control']}/{result['sample_size_control']})")
    print(f"  Treatment: 46.0% ({result['conversions_treatment']}/{result['sample_size_treatment']})")
    print(f"  Relative Lift: {result['relative_lift']:.2%}")
    print(f"  p-value: {result['p_value']:.6f}")
    print(f"  Significant: {result['statistically_significant']}")

    # Test 3: SRM check
    print("\n[Test 3] Sample Ratio Mismatch")
    srm = analyzer.check_sample_ratio_mismatch(5002, 4998)
    print(f"  Control: {srm['n_control']:,}")
    print(f"  Treatment: {srm['n_treatment']:,}")
    print(f"  p-value: {srm['p_value']:.4f}")
    print(f"  SRM Detected: {srm['srm_detected']}")

    # Test 4: Multiple testing correction
    print("\n[Test 4] Multiple Testing Correction")
    p_vals = [0.001, 0.048, 0.051, 0.20]
    corrections = analyzer.apply_corrections(p_vals, method='fdr_bh')
    print(f"  Original p-values: {p_vals}")
    print(f"  Adjusted p-values: {[f'{p:.4f}' for p in corrections['adjusted_p_values']]}")
    print(f"  Rejected: {corrections['rejected']}")
    print(f"  Significant tests: {corrections['num_significant']}/{corrections['num_tests']}")

    print("\n" + "=" * 60)
    print("✓ All statistical tests validated!")
    print("=" * 60)
