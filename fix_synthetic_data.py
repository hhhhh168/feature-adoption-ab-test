"""
Automated fix script for synthetic data red flags
Addresses the critical issues found in audit_red_flags.py

Run this after reviewing VALIDATION_REPORT.md
"""

import os
import re

print("=" * 70)
print("SYNTHETIC DATA RED FLAG FIX SCRIPT")
print("=" * 70)
print()

fixes_applied = []
warnings = []

# ============================================================================
# FIX 1: Update baseline conversion rate in config.py
# ============================================================================
print("[FIX 1] Updating baseline conversion rate...")
print("-" * 70)

config_file = 'src/config.py'
with open(config_file, 'r') as f:
    config_content = f.read()

# Find and replace tier1_completion_rate
old_rate = 'tier1_completion_rate: float = 0.40'
new_rate = 'tier1_completion_rate: float = 0.06  # 6% - realistic for verification flows'

if old_rate in config_content:
    config_content = config_content.replace(old_rate, new_rate)

    with open(config_file, 'w') as f:
        f.write(config_content)

    print("✓ Changed tier1_completion_rate from 40% to 6%")
    print("  (Realistic for email verification flows)")
    fixes_applied.append("Baseline conversion rate: 40% → 6%")
else:
    print("⚠️  Could not find exact match for tier1_completion_rate")
    print("  Please manually edit src/config.py line ~84")
    warnings.append("Manual config edit may be needed")

print()

# ============================================================================
# FIX 2: Update tier2 rate proportionally
# ============================================================================
print("[FIX 2] Updating tier2 completion rate proportionally...")
print("-" * 70)

with open(config_file, 'r') as f:
    config_content = f.read()

old_t2_rate = 'tier2_completion_rate: float = 0.25'
new_t2_rate = 'tier2_completion_rate: float = 0.15  # 15% of those who completed tier1'

if old_t2_rate in config_content:
    config_content = config_content.replace(old_t2_rate, new_t2_rate)

    with open(config_file, 'w') as f:
        f.write(config_content)

    print("✓ Changed tier2_completion_rate from 25% to 15%")
    fixes_applied.append("Tier2 completion rate: 25% → 15%")
else:
    print("⚠️  Could not update tier2_completion_rate automatically")
    warnings.append("Check tier2 rate manually")

print()

# ============================================================================
# FIX 3: Add device-based conversion differences to generator
# ============================================================================
print("[FIX 3] Adding device-based conversion multipliers...")
print("-" * 70)

generator_file = 'src/synthetic_data_generator.py'
with open(generator_file, 'r') as f:
    generator_lines = f.readlines()

# Find the line where completion_rate is first calculated (around line 376)
device_code_added = False
for i, line in enumerate(generator_lines):
    # Look for: completion_rate = self.config.tier1_completion_rate
    if 'completion_rate = self.config.tier1_completion_rate' in line and 'tier1_completion_rate' in line:
        # Check if device multiplier already exists
        if i > 0 and 'device_multiplier' in generator_lines[i-1]:
            print("✓ Device multiplier already exists")
            device_code_added = True
            break

        # Insert device multiplier logic before this line
        indent = '                '  # Match existing indentation
        device_code = [
            f'{indent}# Device type affects conversion (iOS converts 1.3x Android)\n',
            f'{indent}device_multiplier = 1.3 if user.get("device_type") == "iOS" else 1.0\n',
            f'{indent}\n',
        ]

        # Modify the completion_rate line to use multiplier
        generator_lines[i] = line.replace(
            'self.config.tier1_completion_rate',
            'self.config.tier1_completion_rate * device_multiplier'
        )

        # Insert device code before the modified line
        for j, code_line in enumerate(device_code):
            generator_lines.insert(i + j, code_line)

        device_code_added = True
        print("✓ Added device type conversion multiplier (iOS 1.3x Android)")
        fixes_applied.append("Device conversion differences: iOS 1.3x Android")
        break

if device_code_added:
    with open(generator_file, 'w') as f:
        f.writelines(generator_lines)
else:
    print("⚠️  Could not automatically add device multiplier")
    print("  Please manually edit src/synthetic_data_generator.py")
    print("  Add before line ~386:")
    print("    device_multiplier = 1.3 if user.get('device_type') == 'iOS' else 1.0")
    print("    completion_rate = self.config.tier1_completion_rate * device_multiplier")
    warnings.append("Manual device multiplier code needed")

print()

# ============================================================================
# FIX 4: Update README to remove SDV claims
# ============================================================================
print("[FIX 4] Updating README to match actual implementation...")
print("-" * 70)

readme_file = 'README.md'
with open(readme_file, 'r') as f:
    readme_content = f.read()

# Fix 1: Line 32 - "using SDV"
sdv_claim1 = '50,000 realistic user profiles using SDV (Synthetic Data Vault)'
sdv_fix1 = '50,000 realistic user profiles using scipy/numpy statistical distributions'

if sdv_claim1 in readme_content:
    readme_content = readme_content.replace(sdv_claim1, sdv_fix1)
    print("✓ Updated feature description (removed SDV claim)")
else:
    print("⚠️  Feature description not found exactly")

# Fix 2: Line 372 - "using SDV library"
sdv_claim2 = '**This project uses 100% synthetic data generated with the SDV library.**'
sdv_fix2 = '**This project uses 100% synthetic data generated using scipy statistical distributions.**'

if sdv_claim2 in readme_content:
    readme_content = readme_content.replace(sdv_claim2, sdv_fix2)
    print("✓ Updated disclaimer section (removed SDV claim)")
else:
    print("⚠️  Disclaimer not found exactly")

fixes_applied.append("README: Removed misleading SDV claims")

with open(readme_file, 'w') as f:
    f.write(readme_content)

print()

# ============================================================================
# FIX 5: Add limitations section to README
# ============================================================================
print("[FIX 5] Adding limitations section to README...")
print("-" * 70)

limitations_section = """
### Known Limitations

For demonstration purposes, this synthetic dataset includes simplifications:

- **Baseline rates**: Calibrated to 6% for verification flows (realistic for email verification)
- **Sample size**: Demo uses 5,000 users; full implementation designed for 50K+
- **Duration**: 2-week experiment for demonstration; production tests often run 4+ weeks
- **User segments**: Simplified engagement tiers; real apps track dozens of behavioral cohorts
- **Verification flow**: Two-tier system is simplified from real multi-step flows

These simplifications allow the project to demonstrate statistical methodology
while remaining accessible for portfolio review. The statistical techniques
(CUPED, power analysis, SRM checks, multiple testing corrections) scale directly
to production systems with larger sample sizes and longer durations.

**Statistical validity**: All techniques used (variance reduction, power analysis,
multiple testing corrections) follow industry best practices from companies like
Microsoft, Netflix, and Google.
"""

# Find where to insert (after Synthetic Data Disclaimer section)
disclaimer_marker = "The synthetic data is designed to demonstrate technical capabilities and statistical methodology."

if disclaimer_marker in readme_content:
    readme_content = readme_content.replace(
        disclaimer_marker,
        disclaimer_marker + limitations_section
    )

    with open(readme_file, 'w') as f:
        f.write(readme_content)

    print("✓ Added comprehensive limitations section")
    fixes_applied.append("Added limitations section to README")
else:
    print("⚠️  Could not find insertion point for limitations")
    print("  Please manually add limitations section after line ~373")
    warnings.append("Manual limitations section needed")

print()

# ============================================================================
# FIX 6: Update tier1_start_rate for realistic attempt rates
# ============================================================================
print("[FIX 6] Updating tier1_start_rate for realism...")
print("-" * 70)

with open(config_file, 'r') as f:
    config_content = f.read()

old_start_rate = 'tier1_start_rate: float = 0.75'
new_start_rate = 'tier1_start_rate: float = 0.85  # 85% of users attempt verification'

if old_start_rate in config_content:
    config_content = config_content.replace(old_start_rate, new_start_rate)

    with open(config_file, 'w') as f:
        f.write(config_content)

    print("✓ Changed tier1_start_rate from 75% to 85%")
    print("  (Higher attempt rate with lower completion rate = realistic funnel)")
    fixes_applied.append("Tier1 start rate: 75% → 85%")
else:
    print("⚠️  Could not update tier1_start_rate")

print()

# ============================================================================
# SUMMARY
# ============================================================================
print("=" * 70)
print("FIX SUMMARY")
print("=" * 70)
print()

if fixes_applied:
    print(f"✅ Applied {len(fixes_applied)} fixes:")
    for i, fix in enumerate(fixes_applied, 1):
        print(f"  {i}. {fix}")
else:
    print("⚠️  No fixes were applied")

print()

if warnings:
    print(f"⚠️  {len(warnings)} manual actions needed:")
    for i, warning in enumerate(warnings, 1):
        print(f"  {i}. {warning}")
    print()

print("NEXT STEPS:")
print("-" * 70)
print("1. Review the changes above")
print("2. Regenerate data: python scripts/generate_sample_data.py")
print("3. Re-run audit: python audit_red_flags.py")
print("4. Check validation plots: python generate_validation_plots.py")
print()
print("Expected results after regenerating:")
print("  • Baseline conversion: ~6% (down from 29.6%)")
print("  • iOS vs Android: ~1.3x difference (realistic)")
print("  • Documentation: Accurate and honest")
print("  • All 6 audit checks: Should PASS")
print()
print("=" * 70)
