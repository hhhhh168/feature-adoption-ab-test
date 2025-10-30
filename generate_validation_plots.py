"""
Generate validation plots for portfolio review
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

print("Generating validation plots...")

# Load data
assignments = pd.read_csv('data/experiment_assignments.csv')
verification = pd.read_csv('data/verification_attempts.csv')
events = pd.read_csv('data/events.csv')

# Merge for main analysis
verification_tier1 = verification[verification['verification_tier'] == 1].copy()
df = assignments.merge(verification_tier1[['user_id', 'completion_status', 'attempt_timestamp']],
                       on='user_id', how='left')
df['converted'] = (df['completion_status'] == 'completed').fillna(False).astype(int)
df['timestamp'] = pd.to_datetime(df['attempt_timestamp'])

# Create figure with subplots
fig = plt.figure(figsize=(16, 10))

# ============================================================================
# Plot 1: Daily Conversion Rate
# ============================================================================
ax1 = plt.subplot(2, 3, 1)
daily_stats = df.groupby([df['timestamp'].dt.date, 'variant'])['converted'].mean().unstack()
daily_stats.plot(ax=ax1, marker='o', linewidth=2)
ax1.set_title('Daily Conversion Rate by Variant', fontsize=12, fontweight='bold')
ax1.set_xlabel('Date')
ax1.set_ylabel('Conversion Rate')
ax1.legend(['Control', 'Treatment'])
ax1.grid(True, alpha=0.3)

# ============================================================================
# Plot 2: Effect Size Distribution
# ============================================================================
ax2 = plt.subplot(2, 3, 2)
control_rate = df[df['variant'] == 'control']['converted'].mean()
treatment_rate = df[df['variant'] == 'treatment']['converted'].mean()

bars = ax2.bar(['Control', 'Treatment'], [control_rate, treatment_rate],
               color=['lightblue', 'lightgreen'], edgecolor='black', linewidth=1.5)
ax2.set_title('Conversion Rate by Variant', fontsize=12, fontweight='bold')
ax2.set_ylabel('Conversion Rate')
ax2.set_ylim(0, max(control_rate, treatment_rate) * 1.2)

# Add value labels
for bar in bars:
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.1%}', ha='center', va='bottom', fontsize=10, fontweight='bold')

lift = (treatment_rate - control_rate) / control_rate * 100
ax2.text(0.5, ax2.get_ylim()[1] * 0.9, f'Relative Lift: {lift:.1f}%',
         ha='center', transform=ax2.transAxes, fontsize=10,
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
ax2.grid(True, alpha=0.3, axis='y')

# ============================================================================
# Plot 3: Sample Size Distribution
# ============================================================================
ax3 = plt.subplot(2, 3, 3)
variant_counts = df['variant'].value_counts()
bars = ax3.bar(variant_counts.index, variant_counts.values,
               color=['lightblue', 'lightgreen'], edgecolor='black', linewidth=1.5)
ax3.set_title('Sample Size by Variant', fontsize=12, fontweight='bold')
ax3.set_ylabel('Number of Users')

# Add value labels and percentages
for bar in bars:
    height = bar.get_height()
    pct = height / len(df) * 100
    ax3.text(bar.get_x() + bar.get_width()/2., height,
            f'{int(height):,}\n({pct:.1f}%)', ha='center', va='bottom', fontsize=9)

ax3.grid(True, alpha=0.3, axis='y')

# ============================================================================
# Plot 4: Device Type Segmentation
# ============================================================================
ax4 = plt.subplot(2, 3, 4)
device_analysis = df.groupby(['device_type', 'variant'])['converted'].mean().unstack()
device_analysis.plot(kind='bar', ax=ax4, width=0.7, edgecolor='black', linewidth=1.5)
ax4.set_title('Conversion Rate by Device Type', fontsize=12, fontweight='bold')
ax4.set_xlabel('Device Type')
ax4.set_ylabel('Conversion Rate')
ax4.legend(['Control', 'Treatment'])
ax4.set_xticklabels(ax4.get_xticklabels(), rotation=0)
ax4.grid(True, alpha=0.3, axis='y')

# ============================================================================
# Plot 5: Session Count Distribution (Benford Check)
# ============================================================================
ax5 = plt.subplot(2, 3, 5)
session_counts = events.groupby('user_id').size().values

# Get first digits
first_digits = [int(str(abs(x))[0]) for x in session_counts if x > 0]
observed = np.bincount(first_digits, minlength=10)[1:]

# Expected Benford distribution
benford_expected = np.array([30.1, 17.6, 12.5, 9.7, 7.9, 6.7, 5.8, 5.1, 4.6])

x = np.arange(1, 10)
width = 0.35
bars1 = ax5.bar(x - width/2, observed/sum(observed)*100, width, label='Observed',
                color='steelblue', edgecolor='black', linewidth=1.5)
bars2 = ax5.bar(x + width/2, benford_expected, width, label='Benford Expected',
                color='orange', alpha=0.7, edgecolor='black', linewidth=1.5)

ax5.set_title("Benford's Law Check (Session Counts)", fontsize=12, fontweight='bold')
ax5.set_xlabel('First Digit')
ax5.set_ylabel('Percentage (%)')
ax5.legend()
ax5.grid(True, alpha=0.3, axis='y')

# ============================================================================
# Plot 6: Confidence Interval Visualization
# ============================================================================
ax6 = plt.subplot(2, 3, 6)

# Calculate confidence intervals
from scipy.stats import norm

def proportion_ci(successes, total, alpha=0.05):
    p = successes / total
    z = norm.ppf(1 - alpha/2)
    se = np.sqrt(p * (1 - p) / total)
    return p - z * se, p + z * se

control_n = len(df[df['variant'] == 'control'])
control_successes = df[df['variant'] == 'control']['converted'].sum()
treatment_n = len(df[df['variant'] == 'treatment'])
treatment_successes = df[df['variant'] == 'treatment']['converted'].sum()

control_ci = proportion_ci(control_successes, control_n)
treatment_ci = proportion_ci(treatment_successes, treatment_n)

# Plot
variants = ['Control', 'Treatment']
means = [control_rate, treatment_rate]
errors = [
    [control_rate - control_ci[0], treatment_rate - treatment_ci[0]],
    [control_ci[1] - control_rate, treatment_ci[1] - treatment_rate]
]

ax6.errorbar(variants, means, yerr=errors, fmt='o', markersize=10,
             capsize=10, capthick=2, linewidth=2, color='darkblue')
ax6.set_title('95% Confidence Intervals', fontsize=12, fontweight='bold')
ax6.set_ylabel('Conversion Rate')
ax6.grid(True, alpha=0.3, axis='y')

# Add significance indicator
if treatment_ci[0] > control_ci[1]:
    ax6.text(0.5, ax6.get_ylim()[1] * 0.95, '⭐ Statistically Significant',
             ha='center', transform=ax6.transAxes, fontsize=10,
             bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7))

plt.tight_layout()
plt.savefig('validation_plots.png', dpi=150, bbox_inches='tight')
print("✓ Saved validation_plots.png")

# ============================================================================
# Additional Plot: Funnel Analysis
# ============================================================================
fig2, ax = plt.subplots(1, 1, figsize=(10, 6))

# Calculate funnel stages
funnel_data = []
for variant in ['control', 'treatment']:
    variant_df = df[df['variant'] == variant]

    total_users = len(variant_df)
    attempted = variant_df['completion_status'].notna().sum()
    converted = variant_df['converted'].sum()

    funnel_data.append({
        'variant': variant,
        'Total Users': total_users,
        'Started Verification': attempted,
        'Completed Verification': converted
    })

funnel_df = pd.DataFrame(funnel_data).set_index('variant')

# Plot
funnel_df.T.plot(kind='bar', ax=ax, width=0.7, edgecolor='black', linewidth=1.5)
ax.set_title('Verification Funnel by Variant', fontsize=14, fontweight='bold')
ax.set_xlabel('Funnel Stage')
ax.set_ylabel('Number of Users')
ax.legend(['Control', 'Treatment'], title='Variant')
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('funnel_analysis.png', dpi=150, bbox_inches='tight')
print("✓ Saved funnel_analysis.png")

print("\nAll validation plots generated successfully!")
