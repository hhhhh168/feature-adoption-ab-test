"""
Unit tests for statistical analysis functions
"""
import pytest
import numpy as np
import pandas as pd
from src.statistical_analysis import ABTestAnalyzer


class TestABTestAnalyzer:
    """Test suite for ABTestAnalyzer"""

    def setup_method(self):
        """Set up test fixtures"""
        self.analyzer = ABTestAnalyzer(alpha=0.05, power=0.80)

    def test_initialization(self):
        """Test analyzer initialization"""
        assert self.analyzer.alpha == 0.05
        assert self.analyzer.power == 0.80

    def test_sample_size_calculation(self):
        """Test sample size calculation"""
        n = self.analyzer.calculate_sample_size(
            baseline_rate=0.40,
            mde=0.15
        )
        assert isinstance(n, int)
        assert n > 1000  # Should be reasonable
        assert n < 10000

    def test_proportion_test_significant(self):
        """Test proportion test with significant difference"""
        result = self.analyzer.proportion_test(
            control_conversions=400,
            control_total=1000,
            treatment_conversions=460,
            treatment_total=1000
        )

        assert result['p_value'] < 0.05
        assert result['statistically_significant'] is True
        assert result['relative_lift'] > 0
        assert 'ci_lower' in result
        assert 'ci_upper' in result

    def test_proportion_test_not_significant(self):
        """Test proportion test with no difference"""
        result = self.analyzer.proportion_test(
            control_conversions=400,
            control_total=1000,
            treatment_conversions=405,
            treatment_total=1000
        )

        assert result['p_value'] > 0.05
        assert result['statistically_significant'] is False

    def test_t_test_continuous(self):
        """Test t-test for continuous metrics"""
        np.random.seed(42)
        control = np.random.normal(100, 15, 500)
        treatment = np.random.normal(110, 15, 500)  # 10 unit increase

        result = self.analyzer.t_test_continuous(control, treatment)

        assert result['p_value'] < 0.05
        assert result['mean_treatment'] > result['mean_control']
        assert 'cohens_d' in result

    def test_srm_check_balanced(self):
        """Test SRM check with balanced sample"""
        result = self.analyzer.check_sample_ratio_mismatch(
            n_control=5000,
            n_treatment=5000
        )

        assert result['srm_detected'] is False
        assert abs(result['observed_ratio'] - 0.5) < 0.01

    def test_srm_check_imbalanced(self):
        """Test SRM check with imbalanced sample"""
        result = self.analyzer.check_sample_ratio_mismatch(
            n_control=6000,
            n_treatment=4000
        )

        assert result['srm_detected'] is True
        assert result['observed_ratio'] != 0.5

    def test_multiple_testing_correction(self):
        """Test multiple testing corrections"""
        p_values = [0.001, 0.02, 0.048, 0.051, 0.20]

        result = self.analyzer.apply_corrections(p_values, method='fdr_bh')

        assert len(result['adjusted_p_values']) == len(p_values)
        assert result['num_tests'] == 5
        assert all(adj >= orig for adj, orig in zip(result['adjusted_p_values'], p_values))

    def test_post_hoc_power(self):
        """Test post-hoc power calculation"""
        power = self.analyzer.post_hoc_power(
            n_control=1000,
            n_treatment=1000,
            control_rate=0.40,
            treatment_rate=0.46
        )

        assert 0 <= power <= 1
        assert power > 0.8  # Should be well-powered

    def test_analyze_experiment(self):
        """Test comprehensive experiment analysis"""
        np.random.seed(42)

        # Create synthetic experiment data
        n = 1000
        df = pd.DataFrame({
            'user_id': range(n),
            'variant': ['control'] * 500 + ['treatment'] * 500,
            'converted': np.random.binomial(1, 0.40, 500).tolist() +
                        np.random.binomial(1, 0.46, 500).tolist()
        })

        result = self.analyzer.analyze_experiment(
            data=df,
            metrics=['converted'],
            primary_metric='converted'
        )

        assert 'data_quality' in result
        assert 'metric_results' in result
        assert 'recommendation' in result
        assert 'srm_check' in result['data_quality']


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
