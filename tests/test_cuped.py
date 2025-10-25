"""
Unit tests for CUPED implementation
"""
import pytest
import numpy as np
import pandas as pd
from src.cuped import CUPED


class TestCUPED:
    """Test suite for CUPED variance reduction"""

    def setup_method(self):
        """Set up test fixtures"""
        np.random.seed(42)

        # Generate correlated pre and post metrics
        n = 1000
        self.pre_metric = np.random.normal(100, 15, n)
        noise = np.random.normal(0, 10, n)

        # Post-metric correlated with pre-metric (correlation ≈ 0.7)
        self.post_metric = 0.7 * self.pre_metric + 0.3 * noise + 5

        # Add treatment effect
        self.variant = np.array(['control'] * 500 + ['treatment'] * 500)
        self.post_metric[500:] += 10  # Treatment effect

        self.df = pd.DataFrame({
            'user_id': range(n),
            'variant': self.variant,
            'pre_sessions': self.pre_metric,
            'post_sessions': self.post_metric
        })

    def test_adjust_metric_basic(self):
        """Test basic CUPED adjustment"""
        adjusted, var_reduction, theta = CUPED.adjust_metric(
            self.post_metric,
            self.pre_metric,
            self.variant
        )

        assert len(adjusted) == len(self.post_metric)
        assert var_reduction > 0  # Should reduce variance
        assert var_reduction < 1  # Should not eliminate all variance
        assert theta != 0  # Coefficient should be non-zero

    def test_variance_reduction(self):
        """Test that CUPED actually reduces variance"""
        adjusted, var_reduction, _ = CUPED.adjust_metric(
            self.post_metric,
            self.pre_metric
        )

        var_original = np.var(self.post_metric, ddof=1)
        var_adjusted = np.var(adjusted, ddof=1)

        assert var_adjusted < var_original
        assert abs(var_reduction - (var_original - var_adjusted) / var_original) < 0.01

    def test_treatment_effect_preserved(self):
        """Test that CUPED preserves treatment effect"""
        # Original treatment effect
        original_effect = (np.mean(self.post_metric[500:]) -
                          np.mean(self.post_metric[:500]))

        # Adjusted treatment effect
        adjusted, _, _ = CUPED.adjust_metric(
            self.post_metric,
            self.pre_metric,
            self.variant
        )
        adjusted_effect = (np.mean(adjusted[500:]) -
                          np.mean(adjusted[:500]))

        # Effects should be nearly identical (within 1%)
        assert abs(adjusted_effect - original_effect) / abs(original_effect) < 0.01

    def test_apply_to_dataframe(self):
        """Test DataFrame application"""
        df_adjusted = CUPED.apply_to_dataframe(
            self.df,
            'post_sessions',
            'pre_sessions',
            'variant',
            verbose=False
        )

        assert 'post_sessions_cuped' in df_adjusted.columns
        assert len(df_adjusted) == len(self.df)

    def test_validate_assumptions(self):
        """Test assumption validation"""
        validation = CUPED.validate_assumptions(
            self.df,
            'post_sessions',
            'pre_sessions',
            'variant'
        )

        assert 'correlation' in validation
        assert 'pre_metric_balanced' in validation
        assert 'variance_reduction' in validation
        assert validation['sufficient_correlation'] is True
        assert validation['pre_metric_balanced'] is True

    def test_compare_with_without_cuped(self):
        """Test comparison of with/without CUPED"""
        comparison = CUPED.compare_with_without_cuped(
            self.df,
            'post_sessions',
            'pre_sessions',
            'variant'
        )

        assert 'without_cuped' in comparison
        assert 'with_cuped' in comparison
        assert 'variance_reduction' in comparison

        # CUPED should improve p-value
        assert comparison['with_cuped']['p_value'] <= comparison['without_cuped']['p_value']

    def test_zero_variance_pre_metric(self):
        """Test handling of zero variance pre-metric"""
        pre_constant = np.ones(100) * 50  # No variance
        post = np.random.normal(100, 15, 100)

        adjusted, var_reduction, theta = CUPED.adjust_metric(post, pre_constant)

        assert var_reduction == 0.0
        assert theta == 0.0
        assert np.array_equal(adjusted, post)

    def test_uncorrelated_metrics(self):
        """Test CUPED with uncorrelated metrics"""
        np.random.seed(42)
        pre = np.random.normal(100, 15, 1000)
        post = np.random.normal(100, 15, 1000)  # Independent

        adjusted, var_reduction, theta = CUPED.adjust_metric(post, pre)

        # Should have minimal variance reduction
        assert var_reduction < 0.1

    def test_nan_handling(self):
        """Test handling of NaN values"""
        post_with_nan = self.post_metric.copy()
        post_with_nan[0:10] = np.nan

        adjusted, var_reduction, theta = CUPED.adjust_metric(
            post_with_nan,
            self.pre_metric
        )

        # Should still work, ignoring NaN values
        assert not np.all(np.isnan(adjusted))
        assert var_reduction > 0


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
