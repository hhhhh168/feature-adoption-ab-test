"""
Generate sample data for dashboard testing
Run this script to create CSV files for the dashboard
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.synthetic_data_generator import ExperimentDataGenerator
from src.config import DataGenerationConfig, ExperimentConfig

def main():
    """Generate sample data and save to CSV files"""
    print("=" * 60)
    print("GENERATING SAMPLE DATA FOR DASHBOARD")
    print("=" * 60)

    # Create smaller dataset for faster generation
    config = DataGenerationConfig()
    config.n_users = 5000  # Smaller for demo

    exp_config = ExperimentConfig()

    generator = ExperimentDataGenerator(config, exp_config, seed=42)
    data = generator.generate_all_data()

    # Save to CSV
    print("\nSaving data to CSV files...")
    os.makedirs('data', exist_ok=True)

    data['users'].to_csv('data/users.csv', index=False)
    data['pre_metrics'].to_csv('data/user_pre_metrics.csv', index=False)
    data['assignments'].to_csv('data/experiment_assignments.csv', index=False)
    data['events'].to_csv('data/events.csv', index=False)
    data['verification_attempts'].to_csv('data/verification_attempts.csv', index=False)
    data['verification_status'].to_csv('data/verification_status.csv', index=False)

    print("\n✓ Sample data generated successfully!")
    print(f"  Users: {len(data['users']):,}")
    print(f"  Events: {len(data['events']):,}")
    print(f"  Verification Attempts: {len(data['verification_attempts']):,}")
    print("\nYou can now run the dashboard with: streamlit run dashboard/dashboard.py")

if __name__ == "__main__":
    main()
