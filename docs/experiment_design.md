# Experiment Design: Two-Tier Verification Feature Optimization

**Portfolio Project**: This document demonstrates production-grade A/B testing methodology for Data Science, Data Analyst, and Product Analyst roles. All analysis uses synthetic data to showcase experimentation best practices.

---

## Executive Summary

This experiment evaluates whether a streamlined two-tier verification flow increases completion rates in a professional dating application. The redesigned experience aims to improve email verification (Tier 1) and badge/ID verification (Tier 2) through UX optimization.

**Expected Outcome**: 15% relative lift in Tier 1 completion, 20% lift in Tier 2 completion.

---

## 1. Business Context & Problem Statement

### The Problem

A dating application serving educated professionals faces low verification adoption:
- **Current Tier 1 (Email) completion**: 6%
- **Current Tier 2 (Badge/ID) completion**: 15% (of Tier 1 completers)

Low verification rates reduce trust signals on profiles, potentially impacting:
- Match quality and relevance
- User satisfaction and engagement
- Platform safety and authenticity

### Root Cause Analysis

User research and funnel analysis identified friction points:
1. **Complex multi-step flow**: Users abandon during page transitions
2. **Unclear value proposition**: Benefits of verification not communicated upfront
3. **Missing progress indicators**: Users don't know how far they are in the process
4. **Confusing upload instructions**: Badge/ID verification has unclear requirements

### Proposed Solution

Redesigned single-page verification flow featuring:
- Streamlined UX with reduced steps
- Prominent benefits messaging (trust badge, priority matching)
- Real-time progress tracking
- Inline help with visual examples

**Investment**: 3 weeks engineering + design | **Risk**: Low (reversible feature flag)

---

## 2. Hypothesis Development

### Primary Hypothesis (H1)
**"A streamlined verification UX will increase Tier 1 (email) completion rate by at least 15% relative to control"**

**Rationale**: Similar UX simplification experiments (onboarding flows, signup forms) have shown 10-20% lifts. Our changes address multiple identified friction points, making 15% achievable.

### Secondary Hypotheses

**H2**: Tier 2 completion rate increases by ≥20% relative to control
- *Rationale*: Tier 2 has more friction; improvements should have larger impact

**H3**: Users completing verification show higher 7-day engagement (sessions)
- *Rationale*: Verified users have more trust, leading to increased app usage

**H4**: Time-to-complete decreases by ≥20%
- *Rationale*: Fewer steps and clearer instructions should accelerate completion

### Overall Evaluation Criterion (OEC)

**Primary OEC**: Tier 1 Completion Rate
- Most critical step; unlocks Tier 2 eligibility
- Direct business impact on trust and match quality
- Measurable within 14-day experiment window

---

## 3. Experiment Design

### 3.1 Design Type
**Randomized Controlled Trial (A/B Test)**
- Two variants: Control (existing flow) vs Treatment (optimized flow)
- Parallel groups design
- Fixed horizon (14 days)

### 3.2 Randomization Strategy

**Unit of Randomization**: Individual user (at signup)

**Assignment Mechanism**: Hash-based deterministic assignment
```python
hash_value = int(hashlib.md5(f"{user_id}:{experiment_id}".encode()).hexdigest(), 16)
variant = 'control' if hash_value % 2 == 0 else 'treatment'
```

**Benefits of Hash-based Assignment**:
- Deterministic: Same user always gets same variant
- Stateless: No database lookup required
- Consistent: Works across distributed systems
- Independent: Each experiment has independent randomization

**Traffic Allocation**: 50/50 split (control/treatment)

**Stratification**: Pre-stratified by age group, gender, device type to ensure balance

### 3.3 Eligibility & Exclusion

**Included**:
- New signups during experiment period
- Users who haven't completed verification

**Excluded**:
- Existing verified users
- Internal employees (@company.com emails)
- Users in other active verification experiments
- Users who opted out of experiments

### 3.4 Variants

**Control**: Current verification flow
- Separate pages for email and badge upload
- Minimal instructional text
- No progress indicators
- Standard form validation

**Treatment**: Optimized verification flow
- Single-page responsive experience
- Upfront benefits messaging ("Get verified for 3x more matches")
- Real-time progress bar (Step 1 of 2, Step 2 of 2)
- Inline help tooltips with visual examples
- Enhanced error messages with actionable guidance

---

## 4. Power Analysis & Sample Sizing

### 4.1 Statistical Parameters

| Parameter | Value | Justification |
|-----------|-------|---------------|
| Baseline rate (p₀) | 6% | Historical Tier 1 completion |
| Treatment rate (p₁) | 6.9% | 15% relative lift |
| Minimum Detectable Effect | 15% relative | Smallest meaningful business impact |
| Significance level (α) | 0.05 | Industry standard (two-tailed) |
| Statistical power (1-β) | 80% | Industry standard |

### 4.2 Sample Size Calculation

**Formula**: Two-proportion z-test
```
n = 2 * p̄(1-p̄) * (z_{α/2} + z_β)² / (p₁ - p₀)²
```

**Calculation**:
- p̄ = (0.06 + 0.069) / 2 = 0.0645
- z_{α/2} = 1.96 (for α=0.05, two-tailed)
- z_β = 0.84 (for power=0.80)
- Effect size = 0.069 - 0.06 = 0.009

```
n = 2 * 0.0645 * 0.9355 * (1.96 + 0.84)² / (0.009)²
n = 2 * 0.0603 * 7.84 / 0.000081
n ≈ 11,700 per variant
```

**Required**: ~11,700 users per variant (23,400 total)
**Planned**: 25,000 users per variant (50,000 total)
**Demo**: 2,500 per variant (5,000 total) - underpowered for demonstration
**Note**: Demo sample size intentionally smaller; explains why p=0.24 (not significant)

**Decision Rationale**: Over-powering the experiment enables:
- Detection of smaller effects (practical significance)
- Robust subgroup analysis (age, device, engagement level)
- Reduced Type II error risk
- Faster experiment velocity (sufficient sample reached quickly)

### 4.3 Duration Calculation

**Assumptions**:
- Daily new signups: 3,500 users
- Experiment allocation: 100% of traffic
- Users per day entering experiment: 3,500

**Duration** = 50,000 / 3,500 = 14.3 days ≈ **14 days**

**Validation**: 14 days captures 2 full weekly cycles, accounting for day-of-week effects

---

## 5. Metrics Framework

### 5.1 Primary Metric (OEC)

**Tier 1 Completion Rate**

**Definition**:
```sql
Tier 1 Completion Rate = COUNT(DISTINCT user_id WHERE tier1_verified = TRUE)
                        / COUNT(DISTINCT user_id WHERE assigned_to_experiment)
```

**Success Criteria**: Statistically significant increase (p < 0.05 post-FDR correction)

**Business Impact**:
- 15% lift = ~7,500 additional verified users annually
- Estimated revenue impact: $150K+ (based on verified user LTV)

### 5.2 Secondary Metrics

| Metric | Definition | Statistical Test | Target |
|--------|------------|------------------|--------|
| **Tier 2 Completion Rate** | % of Tier 1 users completing Tier 2 | Two-proportion z-test | +20% |
| **Time to Complete (Tier 1)** | Median seconds from start to completion | Welch's t-test | -20% |
| **7-Day Sessions** | Avg sessions 7 days post-verification | T-test (CUPED) | +10% |
| **Verification Start Rate** | % of users who begin verification | Two-proportion z-test | No degradation |

### 5.3 Guardrail Metrics

Metrics to detect negative side effects:

| Metric | Threshold | Action if Triggered |
|--------|-----------|---------------------|
| **Fraud Rate** | >10% increase | Immediate investigation |
| **Support Tickets** | >15% increase | Review UX clarity |
| **App Crashes** | >5% increase | Technical investigation |
| **Verification Reversals** | >5% increase | Review fraud detection |

### 5.4 Diagnostic Metrics

For learning and iteration:
- Step-by-step completion rates (funnel analysis)
- Error rate by verification type
- Time spent per step
- Device type performance differences

---

## 6. Statistical Analysis Plan

### 6.1 Primary Analysis

**Method**: Two-proportion z-test (Intention-to-Treat)

**Hypotheses**:
- H₀: p_treatment - p_control = 0
- H₁: p_treatment - p_control ≠ 0 (two-tailed)

**Test Statistic**:
```
z = (p̂_treatment - p̂_control) / SE_pooled
where SE_pooled = √[p̂_pooled(1-p̂_pooled)(1/n_c + 1/n_t)]
```

**Confidence Interval** (95%):
```
(p̂_treatment - p̂_control) ± 1.96 * SE_unpooled
```

**Significance Level**: α = 0.05 (two-tailed)

### 6.2 Variance Reduction: CUPED

**CUPED** (Controlled-experiment Using Pre-Experiment Data) reduces variance by leveraging pre-experiment covariates.

**Formula**:
```
Y_adjusted = Y - θ(X - E[X])
where θ = Cov(Y,X) / Var(X)
```

**Covariates for this experiment**:
- Pre-experiment sessions (14-day window before signup)
- Pre-experiment profile views
- Pre-experiment matches

**Expected Impact**:
- Variance reduction: 30-50%
- Power increase: 1.3-1.5x
- Enables detection of smaller effects

**Implementation**:
```python
from src.cuped import CUPED

adjusted_metric, var_reduction, theta = CUPED.adjust_metric(
    post_metric=post_sessions,
    pre_metric=pre_sessions,
    variant=variant_assignment
)
```

### 6.3 Multiple Testing Correction

**Problem**: Testing 4 secondary metrics increases false positive risk

**Solution**: Benjamini-Hochberg False Discovery Rate (FDR) control

**Method**:
1. Rank p-values: p₁ ≤ p₂ ≤ ... ≤ p₄
2. Find largest k where p_k ≤ (k/4) * α
3. Reject H₀ for all tests i ≤ k

**Advantage over Bonferroni**: More powerful for multiple hypothesis testing while controlling FDR

### 6.4 Subgroup Analysis (Exploratory)

**Subgroups to analyze**:
- Age cohorts: 18-24, 25-34, 35+
- Device type: iOS vs Android
- Pre-engagement: High (>10 sessions) vs Low (≤10 sessions)
- Geographic region: Urban vs non-urban

**Note**: No α-adjustment for exploratory analyses; results inform future hypotheses, not launch decisions

### 6.5 Sensitivity Analysis

**Scenarios to test**:
1. **Per-protocol analysis**: Users who viewed verification page (vs ITT)
2. **Time window sensitivity**: 3-day, 7-day, 14-day windows
3. **Outlier treatment**: With/without extreme values
4. **Missing data**: Complete case analysis vs imputation

---

## 7. Data Quality Framework

### 7.1 Pre-Launch Validation (A/A Test)

**Execute 2-day A/A test** before launching A/B test:
- Assign users randomly to two identical control variants
- Verify no significant differences (all p-values > 0.05)
- Validates instrumentation, randomization, and pipeline

### 7.2 Sample Ratio Mismatch (SRM) Detection

**What is SRM?**
Sample Ratio Mismatch occurs when observed assignment ratio differs from expected ratio, indicating data quality issues.

**Detection Method**: Chi-squared goodness-of-fit test
```
χ² = Σ (Observed_i - Expected_i)² / Expected_i
```

**Monitoring**:
- **Frequency**: Daily automated check
- **Threshold**: p < 0.01 (more conservative than 0.05)
- **Action**: Pause experiment, investigate root cause

**Common SRM Causes** (Microsoft Research):
- Logging bugs (events not captured for one variant)
- Bot traffic affecting one variant differently
- Performance issues (page load timeout in one variant)
- Incorrect user ID assignment

### 7.3 Covariate Balance Checks

**Purpose**: Validate randomization effectiveness

**Method**: T-tests on pre-experiment metrics across variants
```sql
SELECT
    variant,
    AVG(age) as avg_age,
    AVG(pre_sessions_count) as avg_pre_sessions,
    AVG(pre_matches_count) as avg_pre_matches
FROM experiment_data
GROUP BY variant
```

**Success Criteria**: All p-values > 0.05 (no significant imbalances)

### 7.4 Data Pipeline Monitoring

**Real-time checks**:
- Event latency < 5 minutes
- Event loss rate < 0.1%
- Assignment logging coverage = 100%

**Alerts**:
- Automated Slack alerts for anomalies
- Dashboard for real-time monitoring
- Daily email summary to stakeholders

---

## 8. Decision Framework

### 8.1 Launch Decision Criteria

**Ship Treatment if ALL conditions met**:
1. ✅ Primary metric: p < 0.05 (post-FDR correction) AND positive lift
2. ✅ Practical significance: Relative lift ≥ 5%
3. ✅ No SRM detected: p > 0.01 on chi-squared test
4. ✅ Guardrail metrics: No significant degradation
5. ✅ Secondary metrics: Directionally positive (majority)

**Confidence Level Required**: 95% (α = 0.05)

### 8.2 Iteration Criteria

**Continue running if**:
- Directionally positive but not statistically significant (p < 0.10)
- Can extend to 21 days maximum
- No safety or guardrail concerns

**Design follow-up experiment if**:
- Subgroup analysis shows strong effects in specific segments
- Qualitative feedback suggests specific improvements

### 8.3 Kill Criteria (Do Not Ship)

**Immediate stop if**:
- Significant negative impact on primary metric (p < 0.05)
- SRM detected and cannot be resolved
- Fraud rate increase >10%
- Critical bugs or user complaints
- Guardrail metrics severely degraded

---

## 9. Implementation & Monitoring

### 9.1 Technical Architecture

**Tech Stack**:
- **Randomization**: Python (MD5 hashing)
- **Feature flags**: LaunchDarkly / Custom service
- **Data warehouse**: PostgreSQL (Supabase)
- **Analysis**: Python (pandas, scipy, statsmodels)
- **Visualization**: Plotly, Streamlit

**Event Instrumentation**:
```javascript
// Track verification start
trackEvent('verification_started', {
  user_id: userId,
  experiment_id: 'verification_v1',
  variant: assignedVariant,
  tier: 1,
  timestamp: Date.now()
});
```

### 9.2 Experiment Lifecycle

| Phase | Duration | Activities | Stakeholders |
|-------|----------|-----------|--------------|
| **Design** | 1 week | Finalize metrics, write specs, get approvals | PM, DS, Eng, Design |
| **Development** | 2 weeks | Implement treatment variant, instrumentation | Engineering, Design |
| **QA** | 1 week | Test implementation, validate events, A/A test | QA, Data Engineering |
| **Ramp-up** | 2 days | 10% → 50% traffic gradually | Engineering, DS |
| **Full Run** | 14 days | 100% of new users | DS (monitoring) |
| **Analysis** | 2 days | Statistical analysis, decision | DS, PM |
| **Rollout** | 1 week | 100% launch (if positive) | Engineering |

### 9.3 Monitoring Cadence

**Daily** (Automated):
- SRM checks
- Assignment volume
- Event latency
- Crash rates

**Weekly** (Manual):
- Interim directional results (no peeking problem - for monitoring only)
- Qualitative user feedback review
- Stakeholder sync

**Post-Experiment**:
- Final statistical analysis with corrections
- Comprehensive results report
- Launch recommendation presentation

---

## 10. Risk Assessment & Mitigation

| Risk | Probability | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| **Insufficient statistical power** | Low | High | Over-powered design (50K users vs 2K required) |
| **Novelty effect** | Medium | Medium | 14-day duration; monitor daily trends |
| **Increased fraud attempts** | Low | High | Guardrail metrics; manual review sample |
| **SRM / technical bugs** | Medium | Critical | Daily monitoring; automated alerts; A/A test |
| **Negative secondary impacts** | Low | Medium | Comprehensive guardrail metrics |
| **Seasonal effects** | Low | Low | 14 days spans 2 weeks; balanced sample |
| **Network effects** | Low | Medium | Individual-level randomization minimizes spillover |

---

## 11. Expected Outcomes & Business Impact

### 11.1 Success Scenario (Base Case)

**Results**:
- Primary metric: +15% lift (6% → 6.9%), p < 0.05
- Secondary metrics: Tier 2 +20%, engagement +10%
- Guardrails: No degradation

**Business Impact**:
- **Annual incremental verified users**: ~3,000 (at scale)
- **Estimated revenue impact**: $60K+ (verified user premium LTV)
- **Match quality improvement**: 8-12% (historical correlation)
- **User satisfaction**: +5 NPS points (estimated)

**Decision**: Ship to 100%

### 11.2 Moderate Success Scenario

**Results**:
- Primary metric: +8-12% lift, p < 0.05
- Mixed secondary results

**Decision**: Ship with continued monitoring; iterate based on learnings

### 11.3 Null Result

**Results**:
- No significant difference (p > 0.05)
- Directionally neutral

**Decision**:
- Analyze subgroups for potential targeted treatments
- Design follow-up experiment with alternative hypotheses
- **Learning**: UX simplification alone insufficient; may need incentive layer

---

**About This Document**: This experiment design demonstrates industry-standard A/B testing methodology using synthetic data. The framework is directly applicable to real-world experimentation at technology companies.
