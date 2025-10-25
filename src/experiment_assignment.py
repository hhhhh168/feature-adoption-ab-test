"""
Experiment assignment logic for WorkHeart A/B Testing Platform
Hash-based deterministic randomization for consistent user assignment
"""
import hashlib
from typing import Literal, Optional


class ExperimentAssignment:
    """Stateless experiment assignment using deterministic hashing"""

    @staticmethod
    def assign_variant(
        user_id: str,
        experiment_id: str,
        num_variants: int = 2,
        traffic_allocation: float = 1.0,
        seed: Optional[int] = None
    ) -> Literal['control', 'treatment', 'holdout']:
        """
        Assign user to variant using hash-based randomization

        This method uses deterministic hashing to ensure:
        1. Same user always gets same variant (consistency)
        2. Uniform distribution across variants
        3. Independence from other experiments

        Args:
            user_id: Unique user identifier
            experiment_id: Experiment identifier
            num_variants: Number of variants (default 2 for A/B test)
            traffic_allocation: Fraction of users in experiment (0.0-1.0)
            seed: Optional seed for reproducibility

        Returns:
            Variant assignment: 'control', 'treatment', or 'holdout'

        Example:
            >>> assigner = ExperimentAssignment()
            >>> assigner.assign_variant('user_123', 'exp_001')
            'treatment'
            >>> assigner.assign_variant('user_123', 'exp_001')  # Always same
            'treatment'
        """
        # Create deterministic hash
        hash_input = f"{user_id}:{experiment_id}"
        if seed is not None:
            hash_input = f"{hash_input}:{seed}"

        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)

        # Convert to 0-1 range using modulo
        random_value = (hash_value % 10000) / 10000

        # Check traffic allocation (for ramping experiments)
        if random_value >= traffic_allocation:
            return 'holdout'

        # Assign to variant (50/50 split for A/B test)
        variant_value = hash_value % num_variants
        return 'control' if variant_value == 0 else 'treatment'

    @staticmethod
    def assign_variant_stratified(
        user_id: str,
        experiment_id: str,
        stratum: str,
        num_variants: int = 2
    ) -> Literal['control', 'treatment']:
        """
        Assign variant with stratification

        Stratified randomization ensures balance across important user segments
        (e.g., age groups, device types, engagement levels)

        Args:
            user_id: Unique user identifier
            experiment_id: Experiment identifier
            stratum: Stratification key (e.g., 'age_25-34_ios')
            num_variants: Number of variants

        Returns:
            Variant assignment: 'control' or 'treatment'
        """
        # Include stratum in hash to get independent randomization per stratum
        hash_input = f"{user_id}:{experiment_id}:{stratum}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)

        variant_value = hash_value % num_variants
        return 'control' if variant_value == 0 else 'treatment'

    @staticmethod
    def check_consistency(
        user_id: str,
        experiment_id: str,
        expected_variant: str,
        num_variants: int = 2
    ) -> bool:
        """
        Verify that assignment is consistent

        Args:
            user_id: User identifier
            experiment_id: Experiment identifier
            expected_variant: Expected variant assignment
            num_variants: Number of variants

        Returns:
            True if assignment matches expected variant
        """
        actual = ExperimentAssignment.assign_variant(
            user_id, experiment_id, num_variants
        )
        return actual == expected_variant

    @staticmethod
    def get_assignment_probability(variant: str, num_variants: int = 2) -> float:
        """
        Get theoretical assignment probability for a variant

        Args:
            variant: Variant name
            num_variants: Total number of variants

        Returns:
            Probability of assignment to variant
        """
        if variant == 'holdout':
            return 0.0  # Assuming full traffic allocation
        return 1.0 / num_variants


def validate_assignment_distribution(
    user_ids: list,
    experiment_id: str,
    expected_ratio: float = 0.5,
    tolerance: float = 0.02
) -> dict:
    """
    Validate that assignment distribution is balanced

    Args:
        user_ids: List of user IDs to check
        experiment_id: Experiment identifier
        expected_ratio: Expected control ratio (default 0.5 for 50/50)
        tolerance: Acceptable deviation from expected ratio

    Returns:
        Dictionary with validation results
    """
    assigner = ExperimentAssignment()
    assignments = [
        assigner.assign_variant(uid, experiment_id)
        for uid in user_ids
    ]

    control_count = sum(1 for v in assignments if v == 'control')
    treatment_count = sum(1 for v in assignments if v == 'treatment')
    total = control_count + treatment_count

    actual_ratio = control_count / total if total > 0 else 0
    deviation = abs(actual_ratio - expected_ratio)

    return {
        'control_count': control_count,
        'treatment_count': treatment_count,
        'total': total,
        'actual_ratio': actual_ratio,
        'expected_ratio': expected_ratio,
        'deviation': deviation,
        'is_balanced': deviation <= tolerance,
        'tolerance': tolerance
    }


if __name__ == "__main__":
    # Test the assignment logic
    print("=" * 60)
    print("EXPERIMENT ASSIGNMENT VALIDATION")
    print("=" * 60)

    assigner = ExperimentAssignment()

    # Test 1: Consistency
    print("\n[Test 1] Consistency Check")
    user_id = "user_12345"
    exp_id = "verification_v1"

    variant1 = assigner.assign_variant(user_id, exp_id)
    variant2 = assigner.assign_variant(user_id, exp_id)
    variant3 = assigner.assign_variant(user_id, exp_id)

    print(f"  Assignment 1: {variant1}")
    print(f"  Assignment 2: {variant2}")
    print(f"  Assignment 3: {variant3}")
    print(f"  ✅ Consistent: {variant1 == variant2 == variant3}")

    # Test 2: Distribution
    print("\n[Test 2] Distribution Check (10,000 users)")
    test_users = [f"user_{i}" for i in range(10000)]
    validation = validate_assignment_distribution(test_users, exp_id)

    print(f"  Control: {validation['control_count']:,}")
    print(f"  Treatment: {validation['treatment_count']:,}")
    print(f"  Ratio: {validation['actual_ratio']:.4f} (expected: {validation['expected_ratio']})")
    print(f"  Deviation: {validation['deviation']:.4f}")
    print(f"  ✅ Balanced: {validation['is_balanced']}")

    # Test 3: Independence across experiments
    print("\n[Test 3] Independence Across Experiments")
    exp_id_1 = "experiment_1"
    exp_id_2 = "experiment_2"

    same_variant_count = 0
    test_sample = 1000

    for i in range(test_sample):
        uid = f"user_{i}"
        v1 = assigner.assign_variant(uid, exp_id_1)
        v2 = assigner.assign_variant(uid, exp_id_2)
        if v1 == v2:
            same_variant_count += 1

    independence_ratio = same_variant_count / test_sample
    expected_independence = 0.5  # 50% should match by chance

    print(f"  Same variant: {same_variant_count}/{test_sample}")
    print(f"  Ratio: {independence_ratio:.4f} (expected: ~{expected_independence})")
    print(f"  ✅ Independent: {abs(independence_ratio - expected_independence) < 0.05}")

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
