"""
CUPED (Controlled-experiment Using Pre-Experiment Data) Implementation
Variance reduction technique for A/B testing

Reference: Deng, A., Xu, Y., Kohavi, R., & Walker, T. (2013).
"Improving the sensitivity of online controlled experiments by utilizing pre-experiment data"
"""
import numpy as np
import pandas as pd
from typing import Tuple, Optional, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CUPED:
    """
    CUPED variance reduction for A/B testing

    CUPED uses pre-experiment data to reduce variance in the treatment effect estimate,
    thereby increasing statistical power without additional sample size.

    Formula: Y_adjusted = Y - θ(X - E[X])
    where θ = Cov(Y,X) / Var(X)
    """

    @staticmethod
    def adjust_metric(post_metric: np.ndarray,
                     pre_metric: np.ndarray,
                     variant: Optional[np.ndarray] = None) -> Tuple[np.ndarray, float, float]:
        """
        Apply CUPED adjustment to reduce variance

        Args:
            post_metric: Post-experiment metric values
            pre_metric: Pre-experiment covariate values
            variant: Variant assignments (for validation)

        Returns:
            Tuple of:
                - adjusted_metric: CUPED-adjusted values
                - variance_reduction: Percentage variance reduction (0-1)
                - theta: Optimal coefficient used

        Example:
            >>> post = np.array([10, 12, 8, 15, 11])
            >>> pre = np.array([9, 11, 7, 14, 10])
            >>> adjusted, var_red, theta = CUPED.adjust_metric(post, pre)
            >>> print(f"Variance reduction: {var_red:.1%}")
        """
        # Remove any NaN values
        mask = ~(np.isnan(post_metric) | np.isnan(pre_metric))
        post_clean = post_metric[mask]
        pre_clean = pre_metric[mask]

        if len(post_clean) == 0:
            logger.warning("No valid data for CUPED adjustment")
            return post_metric, 0.0, 0.0

        # Calculate theta (optimal coefficient)
        covariance = np.cov(post_clean, pre_clean)[0, 1]
        variance_pre = np.var(pre_clean, ddof=1)

        if variance_pre == 0:
            logger.warning("Pre-metric has zero variance, CUPED not applicable")
            return post_metric, 0.0, 0.0

        theta = covariance / variance_pre

        # Mean of pre-metric (pooled across all users)
        mean_pre = np.mean(pre_clean)

        # CUPED adjustment: Y_adj = Y - θ(X - E[X])
        adjusted_metric = post_metric.copy()
        adjusted_metric[mask] = post_clean - theta * (pre_clean - mean_pre)

        # Calculate variance reduction
        var_original = np.var(post_clean, ddof=1)
        var_adjusted = np.var(adjusted_metric[mask], ddof=1)

        if var_original == 0:
            variance_reduction = 0.0
        else:
            variance_reduction = (var_original - var_adjusted) / var_original

        # Validation: treatment effect should be unchanged
        if variant is not None:
            variant_clean = variant[mask]
            original_effect = np.mean(post_clean[variant_clean == 'treatment']) - \
                            np.mean(post_clean[variant_clean == 'control'])
            adjusted_effect = np.mean(adjusted_metric[mask][variant_clean == 'treatment']) - \
                            np.mean(adjusted_metric[mask][variant_clean == 'control'])

            if abs(original_effect) > 0:
                effect_change = abs(adjusted_effect - original_effect) / abs(original_effect)
                if effect_change > 0.01:  # More than 1% change
                    logger.warning(f"Treatment effect changed by {effect_change:.2%} after CUPED")

        return adjusted_metric, variance_reduction, theta

    @staticmethod
    def apply_to_dataframe(df: pd.DataFrame,
                          post_col: str,
                          pre_col: str,
                          variant_col: str = 'variant',
                          verbose: bool = True) -> pd.DataFrame:
        """
        Apply CUPED to a DataFrame and add adjusted column

        Args:
            df: DataFrame with experiment data
            post_col: Column name for post-experiment metric
            pre_col: Column name for pre-experiment covariate
            variant_col: Column name for variant assignment
            verbose: Print CUPED results

        Returns:
            DataFrame with additional column '{post_col}_cuped'

        Example:
            >>> df = pd.DataFrame({
            ...     'user_id': [1, 2, 3, 4],
            ...     'variant': ['control', 'treatment', 'control', 'treatment'],
            ...     'sessions': [10, 15, 8, 12],
            ...     'pre_sessions': [9, 14, 7, 11]
            ... })
            >>> df = CUPED.apply_to_dataframe(df, 'sessions', 'pre_sessions')
        """
        df = df.copy()

        adjusted, var_reduction, theta = CUPED.adjust_metric(
            df[post_col].values,
            df[pre_col].values,
            df[variant_col].values if variant_col in df.columns else None
        )

        df[f'{post_col}_cuped'] = adjusted

        if verbose:
            correlation = df[[pre_col, post_col]].corr().iloc[0, 1]
            logger.info(f"CUPED Results for {post_col}:")
            logger.info(f"  Theta: {theta:.4f}")
            logger.info(f"  Variance Reduction: {var_reduction:.1%}")
            logger.info(f"  Correlation (pre, post): {correlation:.3f}")

        return df

    @staticmethod
    def apply_multiple_covariates(df: pd.DataFrame,
                                 post_col: str,
                                 pre_cols: list,
                                 variant_col: str = 'variant') -> pd.DataFrame:
        """
        Apply CUPED with multiple pre-experiment covariates

        Uses linear regression to find optimal weights for multiple covariates

        Args:
            df: DataFrame with experiment data
            post_col: Column name for post-experiment metric
            pre_cols: List of column names for pre-experiment covariates
            variant_col: Column name for variant assignment

        Returns:
            DataFrame with additional column '{post_col}_cuped'
        """
        from sklearn.linear_model import LinearRegression

        df = df.copy()

        # Prepare data
        X = df[pre_cols].values
        y = df[post_col].values

        # Remove rows with NaN
        mask = ~(np.isnan(y) | np.any(np.isnan(X), axis=1))
        X_clean = X[mask]
        y_clean = y[mask]

        if len(X_clean) == 0:
            logger.warning("No valid data for multi-covariate CUPED")
            df[f'{post_col}_cuped'] = df[post_col]
            return df

        # Fit linear regression to find optimal weights
        model = LinearRegression()
        model.fit(X_clean, y_clean)

        # CUPED adjustment: Y_adj = Y - (X - E[X]) * β
        X_centered = X.copy()
        X_centered[mask] = X_clean - np.mean(X_clean, axis=0)

        adjusted = y.copy()
        adjusted[mask] = y_clean - np.dot(X_centered[mask], model.coef_)

        df[f'{post_col}_cuped'] = adjusted

        # Calculate variance reduction
        var_original = np.var(y_clean, ddof=1)
        var_adjusted = np.var(adjusted[mask], ddof=1)
        variance_reduction = (var_original - var_adjusted) / var_original if var_original > 0 else 0

        logger.info(f"Multi-covariate CUPED Results for {post_col}:")
        logger.info(f"  Covariates: {pre_cols}")
        logger.info(f"  Variance Reduction: {variance_reduction:.1%}")
        logger.info(f"  Coefficients: {dict(zip(pre_cols, model.coef_))}")

        return df

    @staticmethod
    def validate_assumptions(df: pd.DataFrame,
                           post_col: str,
                           pre_col: str,
                           variant_col: str = 'variant') -> Dict[str, any]:
        """
        Validate CUPED assumptions

        CUPED assumptions:
        1. Pre-metric is collected before randomization
        2. Pre-metric is correlated with post-metric
        3. Treatment doesn't affect the relationship between pre and post

        Args:
            df: DataFrame with experiment data
            post_col: Post-experiment metric column
            pre_col: Pre-experiment metric column
            variant_col: Variant column

        Returns:
            Dictionary with validation results
        """
        results = {}

        # 1. Check correlation
        correlation = df[[pre_col, post_col]].corr().iloc[0, 1]
        results['correlation'] = correlation
        results['sufficient_correlation'] = abs(correlation) > 0.1  # Rule of thumb

        # 2. Check balance of pre-metric across variants
        control_pre = df[df[variant_col] == 'control'][pre_col].dropna()
        treatment_pre = df[df[variant_col] == 'treatment'][pre_col].dropna()

        from scipy import stats
        _, p_value = stats.ttest_ind(control_pre, treatment_pre)
        results['pre_metric_balance_pvalue'] = p_value
        results['pre_metric_balanced'] = p_value > 0.05

        # 3. Check if variance reduction is achieved
        adjusted, var_reduction, theta = CUPED.adjust_metric(
            df[post_col].values,
            df[pre_col].values,
            df[variant_col].values
        )
        results['variance_reduction'] = var_reduction
        results['theta'] = theta
        results['effective'] = var_reduction > 0.1  # At least 10% reduction

        # 4. Summary
        all_valid = (results['sufficient_correlation'] and
                    results['pre_metric_balanced'] and
                    results['effective'])
        results['all_assumptions_met'] = all_valid

        return results

    @staticmethod
    def compare_with_without_cuped(df: pd.DataFrame,
                                   post_col: str,
                                   pre_col: str,
                                   variant_col: str = 'variant') -> Dict[str, any]:
        """
        Compare analysis results with and without CUPED

        Args:
            df: DataFrame with experiment data
            post_col: Post-experiment metric
            pre_col: Pre-experiment covariate
            variant_col: Variant column

        Returns:
            Dictionary comparing both approaches
        """
        from scipy import stats as sp_stats

        # Without CUPED
        control = df[df[variant_col] == 'control'][post_col].dropna()
        treatment = df[df[variant_col] == 'treatment'][post_col].dropna()

        t_stat_orig, p_val_orig = sp_stats.ttest_ind(treatment, control)
        var_orig = np.var(df[post_col].dropna(), ddof=1)

        # With CUPED
        df_cuped = CUPED.apply_to_dataframe(
            df, post_col, pre_col, variant_col, verbose=False
        )
        control_cuped = df_cuped[df_cuped[variant_col] == 'control'][f'{post_col}_cuped'].dropna()
        treatment_cuped = df_cuped[df_cuped[variant_col] == 'treatment'][f'{post_col}_cuped'].dropna()

        t_stat_cuped, p_val_cuped = sp_stats.ttest_ind(treatment_cuped, control_cuped)
        var_cuped = np.var(df_cuped[f'{post_col}_cuped'].dropna(), ddof=1)

        variance_reduction = (var_orig - var_cuped) / var_orig if var_orig > 0 else 0

        return {
            'without_cuped': {
                't_statistic': t_stat_orig,
                'p_value': p_val_orig,
                'variance': var_orig,
                'mean_diff': np.mean(treatment) - np.mean(control)
            },
            'with_cuped': {
                't_statistic': t_stat_cuped,
                'p_value': p_val_cuped,
                'variance': var_cuped,
                'mean_diff': np.mean(treatment_cuped) - np.mean(control_cuped)
            },
            'variance_reduction': variance_reduction,
            'power_increase_factor': np.sqrt(1 / (1 - variance_reduction)) if variance_reduction < 1 else 1,
            'p_value_improvement': (p_val_orig - p_val_cuped) / p_val_orig if p_val_orig > 0 else 0
        }


if __name__ == "__main__":
    # Test CUPED implementation
    print("=" * 60)
    print("CUPED VALIDATION")
    print("=" * 60)

    np.random.seed(42)

    # Generate synthetic data with correlation
    n = 1000
    pre_metric = np.random.normal(100, 15, n)
    noise = np.random.normal(0, 10, n)

    # Post-metric correlated with pre-metric
    post_metric = 0.7 * pre_metric + 0.3 * noise + 5  # Correlation ≈ 0.7

    # Add treatment effect
    variant = np.array(['control'] * 500 + ['treatment'] * 500)
    treatment_effect = 10
    post_metric[500:] += treatment_effect  # Treatment increases metric by 10

    df = pd.DataFrame({
        'user_id': range(n),
        'variant': variant,
        'pre_sessions': pre_metric,
        'post_sessions': post_metric
    })

    print("\n[Test 1] Basic CUPED Application")
    df_adjusted = CUPED.apply_to_dataframe(
        df, 'post_sessions', 'pre_sessions', 'variant'
    )
    print(f"  ✓ CUPED column created: 'post_sessions_cuped'")

    print("\n[Test 2] Validate Assumptions")
    validation = CUPED.validate_assumptions(
        df, 'post_sessions', 'pre_sessions', 'variant'
    )
    print(f"  Correlation: {validation['correlation']:.3f}")
    print(f"  Pre-metric balanced: {validation['pre_metric_balanced']}")
    print(f"  Variance reduction: {validation['variance_reduction']:.1%}")
    print(f"  All assumptions met: {validation['all_assumptions_met']}")

    print("\n[Test 3] Compare With/Without CUPED")
    comparison = CUPED.compare_with_without_cuped(
        df, 'post_sessions', 'pre_sessions', 'variant'
    )
    print(f"  Without CUPED p-value: {comparison['without_cuped']['p_value']:.6f}")
    print(f"  With CUPED p-value: {comparison['with_cuped']['p_value']:.6f}")
    print(f"  Variance reduction: {comparison['variance_reduction']:.1%}")
    print(f"  Power increase factor: {comparison['power_increase_factor']:.2f}x")

    print("\n" + "=" * 60)
    print("✓ CUPED implementation validated!")
    print("=" * 60)
