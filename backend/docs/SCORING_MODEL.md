# CodePilot Scoring Engine — Model Specification v2.0

## 1. Overview

CodePilot uses a deterministic scoring engine that evaluates code quality across four dimensions:
**Security**, **Performance**, **Maintainability**, and **Technical Debt Health**.
These are aggregated into an **Overall Quality** score using a Weighted Sum Model.

> **Important Disclaimer:**
> CodePilot uses established software-quality concepts and a custom deterministic aggregation model.
> The coefficients are initial calibration parameters that require empirical validation.
> No empirical validation results have been fabricated.

---

## 2. Theoretical Foundations

The scoring model draws on established concepts from the software quality literature:

| Concept | Theoretical Precedent | CodePilot Usage |
|---------|----------------------|-----------------|
| Quality characteristics (Security, Performance, Maintainability) | ISO/IEC 25010 Software Quality Model | Used as organizational categories for scoring |
| EffectiveImpact = SeverityWeight × ConfidenceFactor | Structural similarity to Risk = Likelihood × Impact | CodePilot-specific formula; NOT a CVSS score |
| Weighted aggregation of sub-scores | Weighted Sum Model / Multi-Criteria Decision Analysis (MCDA) | Overall Quality uses a WSM with 4 dimensions |
| Issue density normalization by LOC | Defect density metrics (e.g., defects per KLOC) | Used for size-aware Maintainability and Tech Debt |
| Cyclomatic complexity per function | McCabe's Cyclomatic Complexity (1976) | Average complexity per function penalizes Maintainability |

### What This Model Is NOT

- The exact formulas are **not** ISO/IEC 25010 formulas.
- The exact weights are **not** ISO/IEC 25010 importance weights.
- The model is **not** equivalent to CVSS.
- Tech Debt Health is **not** SQALE Technical Debt Ratio.
- The current constants are **not** empirically validated.

---

## 3. CodePilot-Specific Design Choices

### 3.1 Severity Weights

| Severity | Weight |
|----------|--------|
| Critical | 10 |
| High | 7 |
| Medium | 4 |
| Low | 1 |

These are **initial calibration weights — subject to empirical validation**.
They encode the relative damage potential of each severity tier as ordinal weights.

### 3.2 Category Weights (Overall Quality)

| Category | Weight |
|----------|--------|
| Security | 0.30 |
| Performance | 0.25 |
| Maintainability | 0.30 |
| Technical Debt Health | 0.15 |
| **Total** | **1.00** |

These are **initial CodePilot calibration weights, pending empirical validation**.
They are NOT derived from ISO/IEC 25010 or AHP analysis.

### 3.3 Penalty Multipliers

| Multiplier | Value | Used In |
|------------|-------|---------|
| Security penalty | ×3 | SecurityPenalty = 3 × SecurityImpact |
| Performance penalty | ×3 | PerformancePenalty = 3 × PerformanceImpact |
| Tech Debt penalty | ×2 | TechDebtPenalty = 2 × NormalizedImpact |
| Maintainability impact | ×1.5 | MaintPenalty += 1.5 × NormalizedImpact |
| Complexity divisor | ÷2 | MaintPenalty += AverageComplexity / 2 |

All multipliers are **calibration parameters, not established scientific constants**.

---

## 4. Current Formulas

### 4.1 Effective Impact

$$\text{EffectiveImpact}_i = \text{SeverityWeight}_i \times \frac{\text{Confidence}_i}{100}$$

### 4.2 Size Normalization

$$\text{LOC\_K} = \max\!\left(\frac{\text{LOC}}{1000},\ 1.0\right)$$

The minimum guard prevents division by zero and prevents tiny snippets from producing extreme values.

$$\text{NormalizedImpact} = \frac{\text{TotalImpact}}{\text{LOC\_K}}$$

### 4.3 Confidence-Adjusted Issue Count

$$\text{ConfidenceAdjustedIssueCount} = \sum_{i} \frac{\text{Confidence}_i}{100}$$

This replaces the old raw `IssueCount` which was confidence-blind (see §6).

$$\text{NormalizedIssueDensity} = \frac{\text{ConfidenceAdjustedIssueCount}}{\text{LOC\_K}}$$

### 4.4 Average Complexity

$$\text{AverageComplexity} = \frac{\text{TotalCyclomaticComplexity}}{\text{NumberOfFunctions}}$$

If `NumberOfFunctions = 0`, use `TotalCyclomaticComplexity` as fallback.

### 4.5 Security Score

$$\text{SecurityScore} = \text{clamp}\!\left(100 - 3 \times \text{SecurityImpact},\ 0,\ 100\right)$$

### 4.6 Performance Score

$$\text{PerformanceScore} = \text{clamp}\!\left(100 - 3 \times \text{PerformanceImpact},\ 0,\ 100\right)$$

### 4.7 Technical Debt Health

$$\text{TechDebtHealth} = \text{clamp}\!\left(100 - 2 \times \text{NormalizedImpact},\ 0,\ 100\right)$$

This is a CodePilot-specific health metric. It is NOT SQALE Technical Debt Ratio.

### 4.8 Maintainability Score

$$\text{MaintPenalty} = 1.5 \times \text{NormalizedImpact} + \text{NormalizedIssueDensity} + \frac{\text{AverageComplexity}}{2}$$

$$\text{MaintainabilityScore} = \text{clamp}\!\left(100 - \text{MaintPenalty},\ 0,\ 100\right)$$

### 4.9 Maintainability Grade

| Score Range | Grade |
|-------------|-------|
| 90–100 | A |
| 80–89 | B |
| 70–79 | C |
| 60–69 | D |
| < 60 | F |

### 4.10 Overall Quality

$$\text{OverallQuality} = 0.30 \times \text{SecurityScore} + 0.25 \times \text{PerformanceScore} + 0.30 \times \text{MaintainabilityScore} + 0.15 \times \text{TechDebtHealth}$$

---

## 5. Mathematical Properties

### 5.1 Boundedness — All Scores ∈ [0, 100]

**Proof**: Each sub-score is explicitly clamped: `clamp(value, 0, 100)`.
Since each sub-score $S_i \in [0, 100]$ and the category weights satisfy $\sum w_i = 1.0$:

$$\text{OverallQuality} = \sum w_i \times S_i \leq \sum w_i \times 100 = 100$$
$$\text{OverallQuality} = \sum w_i \times S_i \geq \sum w_i \times 0 = 0$$

Therefore $\text{OverallQuality} \in [0, 100]$. ∎

### 5.2 Severity Monotonicity

**Claim**: For the same confidence, `Critical > High > Medium > Low` in effective impact.

**Proof**: The severity weights are strictly ordered: $10 > 7 > 4 > 1$.
For any fixed $c > 0$: $\text{Impact} = w \times (c/100)$.
Since $w$ is strictly ordered, impact is strictly ordered. ∎

**Numerical example** (confidence = 100%):
- Low: $1 \times 1.0 = 1.0$
- Medium: $4 \times 1.0 = 4.0$
- High: $7 \times 1.0 = 7.0$
- Critical: $10 \times 1.0 = 10.0$

### 5.3 Confidence Monotonicity

**Claim**: For the same severity, higher confidence → higher effective impact.

**Proof**: For fixed weight $w > 0$: $\text{Impact} = w \times (c/100)$.
This is strictly increasing in $c$ for $c > 0$. ∎

**Numerical example** (severity = High, weight = 7):
- 10% confidence: $7 \times 0.1 = 0.7$
- 50% confidence: $7 \times 0.5 = 3.5$
- 100% confidence: $7 \times 1.0 = 7.0$

### 5.4 Non-Improvement When Findings Are Added

**Claim**: Adding any issue (with weight ≥ 0 and confidence ≥ 0) cannot improve any score.

**Proof**: Each new issue contributes non-negative additions to `total_impact`,
`confidence_adjusted_issue_count`, and (if categorized) to `security_impact` or `performance_impact`.
All penalty terms are monotonically non-decreasing in these quantities.
Since all scores are computed as $100 - \text{penalty}$, no score can increase. ∎

### 5.5 Complexity Monotonicity

**Claim**: Higher average complexity → lower maintainability score.

**Proof**: The maintainability penalty includes `AverageComplexity / 2`.
This is strictly increasing in `AverageComplexity`.
Since $\text{MaintainabilityScore} = 100 - \text{MaintPenalty}$, the score strictly decreases. ∎

### 5.6 Overall Score Boundedness (Weights Sum to 1)

**Claim**: Since $\sum w_i = 1.0$ exactly, the overall score is a convex combination of the sub-scores.

**Verification**: $0.30 + 0.25 + 0.30 + 0.15 = 1.00$

This guarantees the overall score is bounded by the minimum and maximum sub-scores, preventing arithmetic overflow. ∎

---

## 6. Resolved Bug: Confidence-Blind Issue Count

### The Problem (v1.0)

The old Maintainability formula was:

$$\text{MaintPenalty}_{v1} = 1.5 \times \text{TotalImpact} + \text{IssueCount} + \frac{\text{Complexity}}{2}$$

The `IssueCount` term was the raw number of issues, ignoring confidence entirely.

### Demonstrating the Inconsistency

**Scenario**: 50 Low-severity findings, each at 10% confidence.

| Metric | Calculation | Result |
|--------|-------------|--------|
| EffectiveImpact per issue | $1 \times 0.10$ | $0.1$ |
| TotalImpact | $50 \times 0.1$ | $5.0$ |
| Tech Debt Health (v1) | $100 - (5 \times 2)$ | $90$ |
| **OLD Maint Penalty** | $1.5 \times 5 + \mathbf{50} + 0$ | $\mathbf{57.5}$ |
| **OLD Maintainability** | $100 - 57.5$ | $\mathbf{42.5}$ (Grade F) |

Tech Debt said "90/100 — healthy", while Maintainability said "42/100 — failing".
The discrepancy arose because Tech Debt discounted confidence properly (via EffectiveImpact)
while Maintainability added the **raw count of 50 issues** regardless of how uncertain each one was.

### The Fix (v2.0)

$$\text{MaintPenalty}_{v2} = 1.5 \times \text{NormalizedImpact} + \text{NormalizedIssueDensity} + \frac{\text{AverageComplexity}}{2}$$

Where $\text{NormalizedIssueDensity} = \frac{\text{ConfidenceAdjustedIssueCount}}{\text{LOC\_K}}$
and $\text{ConfidenceAdjustedIssueCount} = \sum (c_i / 100) = 50 \times 0.1 = 5.0$.

| Metric | Calculation | Result |
|--------|-------------|--------|
| ConfidenceAdjustedIssueCount | $50 \times 0.1$ | $5.0$ |
| NormalizedIssueDensity | $5.0 / 1.0$ | $5.0$ |
| **NEW Maint Penalty** | $1.5 \times 5 + 5.0 + 0$ | $\mathbf{12.5}$ |
| **NEW Maintainability** | $100 - 12.5$ | $\mathbf{88}$ (Grade B) |

Tech Debt Health is 90, Maintainability is 88. The scores are now internally consistent.

---

## 7. Known Limitations

1. **Category classification**: Security and Performance categorization relies on keyword matching
   in `rule_type` and `description` fields. This may misclassify some edge cases.

2. **No empirical calibration**: All penalty multipliers (×3, ×2, ×1.5, ÷2) and category weights
   (30/25/30/15) are initial design choices. They have not been calibrated against external benchmarks.

3. **Single-dimension normalization**: LOC is the only size metric used. Alternatives such as
   function count normalization for Security/Performance have not been explored.

4. **Linear penalty model**: All penalty functions are linear. Non-linear models (logarithmic,
   sigmoid) might better capture diminishing returns at extreme issue counts.

5. **No inter-issue interaction**: Each issue's impact is computed independently. Correlated
   issues (e.g., a security vulnerability causing a performance problem) are double-counted.

---

## 8. Empirical Validation Plan

The following validation experiments are planned but have **not yet been performed**:

### Phase 1: Controlled Benchmarks
- **OWASP Benchmark / Juliet Test Suite**: Run CodePilot on known-vulnerable code samples
  and compare Security scores against ground truth.
- **Seeded Defect Experiments**: Inject known defects at various severities into clean code
  and verify score degradation matches expectations.

### Phase 2: Cross-Tool Comparison
- **SonarQube Community Edition**: Run identical codebases through both CodePilot and SonarQube.
- Compare Security, Maintainability, and Technical Debt scores.
- Compute **Spearman's rank correlation coefficient (ρ)** between the tools' rankings.
- Analyze disagreements to identify calibration improvements.

### Phase 3: Metric Validation
- Compare CodePilot's Maintainability score against established metrics such as the
  **Maintainability Index** (MI = 171 − 5.2 ln(V) − 0.23 G − 16.2 ln(LOC)).
- Validate that the scoring model's ordinal rankings agree with MI rankings at an
  acceptable level (e.g., ρ ≥ 0.70).

### Phase 4: Weight Calibration
- Collect expert assessments of code quality for a representative sample.
- Use regression analysis or AHP to derive empirically grounded category weights.
- Compare calibrated weights against the current initial values.

> **Statement**: No benchmark results, correlation coefficients, or cross-tool comparisons
> have been fabricated. All reported scores are deterministic outputs of the documented formulas.
