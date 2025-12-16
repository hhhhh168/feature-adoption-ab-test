# Quick Reference - A/B Test Portfolio Project

## Key Metrics

```
Sample Size:      5,000 users (2,535 control, 2,465 treatment)
Baseline Rate:    5.21%
Treatment Rate:   6.00%
Relative Lift:    15.31%
P-value:          0.244 (not significant)
Test Duration:    14 days
SRM p-value:      0.322 (no issues)
```

---

## Project Summary

This A/B testing platform demonstrates statistical methods for experiment analysis:
- CUPED variance reduction
- Sample Ratio Mismatch detection
- Multiple testing corrections (Benjamini-Hochberg)
- Power analysis and sample size calculations

The experiment tests a streamlined verification flow for a dating app. With 5K users and 6% baseline, the result isn't statistically significant—which is realistic. About a third of real experiments don't show significant results.

---

## Common Interview Questions

**"Tell me about this project"**
- Dating app verification flow optimization
- Used CUPED, SRM detection, power analysis
- Synthetic data with realistic parameters (5% baseline)
- Result wasn't significant (p=0.24), which happens in real experiments

**"Why synthetic data?"**
- Dating app data contains PII
- Lets me demonstrate methodology with known ground truth
- Parameters based on realistic verification flow rates

**"What was the result?"**
- Not statistically significant (p=0.24)
- Shows realistic variance—not all experiments succeed
- Still demonstrates proper methodology

**"What would you do differently in production?"**
- Longer duration (4+ weeks for novelty effects)
- More user segments (geographic, new vs returning)
- Consider sequential testing for early stopping
- Bayesian analysis as a complement to frequentist

---

## Technical Details

**CUPED**
- Formula: Y_adjusted = Y - θ(X - E[X])
- Achieved ~42% variance reduction on sessions metric
- Increases power without needing larger samples

**SRM Detection**
- Chi-squared test for allocation balance
- Threshold: p < 0.01 flags issues
- Result: p = 0.322 (no SRM detected)

**Power Analysis**
- 6% baseline, 15% MDE
- Required: ~11,700 per variant for 80% power
- Demo uses 2,500 per variant (intentionally underpowered)

**Multiple Testing**
- Benjamini-Hochberg FDR control
- Applied when testing multiple metrics

---

## Key Files

```
src/
├── synthetic_data_generator.py  # Data generation
├── statistical_analysis.py      # Statistical tests
├── cuped.py                     # Variance reduction
└── config.py                    # Parameters

dashboard/
└── dashboard.py                 # Streamlit app

tests/
├── test_statistics.py           # Statistical method tests
└── test_cuped.py                # CUPED validation
```

---

## Quick Reminders

1. Baseline: 5.2%, Treatment: 6.0%, Lift: 15.3%
2. P-value: 0.244 (not significant—this is realistic)
3. Sample: 5K users, underpowered for demonstration
4. Methods: CUPED, SRM, Benjamini-Hochberg
5. Data: Synthetic with realistic parameters
