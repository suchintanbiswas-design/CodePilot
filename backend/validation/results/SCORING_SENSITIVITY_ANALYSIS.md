# CodePilot Scoring Sensitivity Analysis

## 1. Objective
Perform a formal sensitivity analysis on the frozen CodePilot Scoring Engine v2.0 parameters. The goal is to determine whether the ranking and scoring conclusions produced by the current baseline coefficients are highly sensitive to reasonable changes, or if they remain mathematically stable (robust).

*Note: This is an analysis-only experiment. No parameters have been optimized or permanently changed based on these results.*

## 2. Baseline Formulas
**Maintainability Score:**
clamp(100 - (α × NormalizedImpact + β × NormalizedIssueDensity + γ × AverageComplexity), 0, 100)

Current Baseline Coefficients:
- α = 1.5
- β = 1.0
- γ = 0.5

**Overall Quality Score:**
Current Baseline Weights:
- Security = 0.30
- Performance = 0.25
- Maintainability = 0.30
- Tech Debt = 0.15

## 3. Parameter Ranges
**Maintainability Grid (27 Configurations):**
- α ∈ [1.0, 1.5, 2.0]
- β ∈ [0.5, 1.0, 1.5]
- γ ∈ [0.25, 0.50, 0.75]

## 4. Overall-Weight Scenarios
Six predefined weight configurations were evaluated:
- **BASELINE**: [S: 0.30, P: 0.25, M: 0.30, T: 0.15]
- **A**: [S: 0.35, P: 0.25, M: 0.25, T: 0.15]
- **B**: [S: 0.25, P: 0.30, M: 0.30, T: 0.15]
- **C**: [S: 0.30, P: 0.20, M: 0.35, T: 0.15]
- **D**: [S: 0.30, P: 0.30, M: 0.25, T: 0.15]
- **E**: [S: 0.30, P: 0.25, M: 0.25, T: 0.20]

## 5. Methodology
- **Data:** The frozen 20-file benchmark dataset (ackend/validation/benchmark/).
- The base metrics (NormalizedImpact, NormalizedIssueDensity, AverageComplexity) were extracted for each file.
- All 27 Maintainability configurations and 6 Overall Quality configurations were recomputed for the entire benchmark.
- Spearman rank correlation, absolute score differences, and ranking reversals (pairs of files that swapped relative positions) were calculated relative to the baseline.

## 6. Results Summary
- **Maintainability configurations tested:** 27
- **Overall-weight configurations tested:** 6
- **Strongest baseline correlation:** ρ = 0.9989 (Maintainability), ρ = 0.9967 (Overall)
- **Weakest baseline correlation:** ρ = 0.9392 (Maintainability), ρ = 0.9936 (Overall)
- **Largest score change:** 25.75 points (extreme α=2.0 combined with high-impact file)
- **Largest ranking reversal count:** 39 (out of 190 possible pairs, ~20.5%)

## 7. Maintainability Sensitivity
Despite altering coefficients by up to ±50%, the Maintainability score proved extremely stable. 
- The Spearman rank correlation across all 27 combinations remained uniformly high (minimum ρ = 0.9392). 
- While the raw scores drifted in extreme configurations (max absolute difference of 25.75 for highly defective files), the relative ordering of the files remained mathematically intact. 
- Top-5 and Bottom-5 file overlap remained consistent across nearly all configurations.

## 8. Overall-Weight Sensitivity
The Overall Quality metric is heavily buffered against small category-weight perturbations (±0.05). 
- Rank correlation remained nearly identical (minimum ρ = 0.9936).
- The maximum mean absolute difference (MAD) across the entire benchmark for any alternative weight configuration was only 0.61 points out of 100.
- Maximum ranking reversals were negligible (11 pairs, < 6%).

## 9. Most Influential Parameters
Using Mean Absolute Difference (MAD) from the baseline as the sensitivity measure:
- **α (NormalizedImpact):** High influence (MAD ~ 2.16)
- **γ (AverageComplexity):** High influence (MAD ~ 1.96)
- **β (NormalizedIssueDensity):** Low influence (MAD ~ 0.43)

*Note: β has a smaller apparent numerical influence because issue counts normalized per 1,000 LOC naturally produce smaller raw values than complexity or weighted severity impacts.*

## 10. Edge Case Analysis
- **Files with zero issues:** Totally insensitive to α and β. Their relative scores are dictated purely by γ (AverageComplexity).
- **Files with high complexity:** Highly sensitive to γ. Increasing γ acts as a strong equalizer that drags visually clean but overly complex code downward.
- **Files near 100:** Remained near 100 across all configurations due to clamping and low raw metrics.

## 11. Interpretation
The current model is defined as **ROBUST**.
*Methodology/Threshold:* A model is considered robust if reasonable coefficient perturbations (±33% to ±50%) result in a minimum Spearman correlation > 0.90, preserving the vast majority of relative rankings and producing graceful score degradation.
*Conclusion:* Small reasonable coefficient changes preserve rankings well and produce structurally similar conclusions. The overall score is exceptionally stable.

## 12. Limitations
- The sample size of 20 files is sufficient for proving mathematical stability but not for large-scale statistical calibration.
- The interaction between confidence clamping and nonlinear issue combinations is not tested here since all variables are linear combinations.
- This analysis operates strictly in the domain of the existing findings and does not account for false positives/negatives generated by the analyzer itself.

## 13. Academic Conclusion
The sensitivity analysis demonstrates strong **parameter stability**. The scoring model behaves deterministically and gracefully under reasonable coefficient perturbations, confirming that the current formulas are not brittle. 

However, mathematical stability must be explicitly distinguished from universal correctness. This analysis proves that the formula does not break or wildly re-rank files if the weights are slightly shifted; it is **not** proof that α=1.5, β=1.0, and γ=0.5 are the perfectly optimized, universally correct coefficients for human maintainability perception. Future empirical calibration against human expert labels is required to transition these stable engineering baselines into optimized psychological metrics.
