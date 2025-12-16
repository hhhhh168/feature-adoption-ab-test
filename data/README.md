# Data Directory

This directory contains generated data files for the A/B testing platform.

## Contents

After running the data generation pipeline, this directory will contain:

- `users.csv` - User demographics and account information
- `user_pre_metrics.csv` - Pre-experiment metrics for CUPED
- `experiment_assignments.csv` - Variant assignments (control/treatment)
- `events.csv` - User interaction event stream
- `verification_attempts.csv` - Verification flow attempts
- `verification_status.csv` - Current verification status

## Note

These files are automatically generated using synthetic data and are **excluded from git** (see `.gitignore`).

To generate data, run:

```bash
python -m src.synthetic_data_generator
```

## Data Privacy

This project uses **100% synthetic data** generated with scipy/numpy statistical distributions. No real user data is included.
