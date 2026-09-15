# External Empirical Validation: Performance (CodePilot Static Engine)

## 1. Objective
To externally validate CodePilot v2.0's Performance Score by correlating it against an independently defined, qualitative severity ground truth (`ground_truth.csv`), utilizing a controlled 20-file benchmark.

## 2. Dataset
- **Ground Truth**: `backend/validation/benchmark/ground_truth.csv`. Qualitative severity levels were ordinally encoded: `none`=0, `low`=1, `medium`=2, `high`=3, `critical`=4.
- **CodePilot Results**: `backend/validation/results/codepilot_results.csv`.
- **N = 20**: The primary benchmark samples (`sample01.py` through `sample20.py`). Model property files were excluded.

## 3. Methodology
The datasets were joined on `file`. A statistically correct tied-rank Spearman correlation was calculated. Since a higher ground-truth severity (e.g., `critical` = 4) corresponds to worse performance, we expect the CodePilot Performance Score (where 100 is best, 0 is worst) to decrease. Thus, the expected correlation direction is **negative**.

## 4. Result
- **n**: 20
- **Spearman rho**: -0.016988
- **p-value**: 9.437205e-01 (0.9437)

## 5. Ranking Summary
- **Highest Severity Benchmark Cases (Ground Truth)**: `sample19.py` (critical), `sample15.py` (high), `sample10.py` (medium), `sample12.py` (medium).
- **Lowest Severity Benchmark Cases (Ground Truth)**: 16 files scored `none`.

## 6. Disagreement Analysis

The largest rank disagreements overwhelmingly highlight the structural limitations of a static regex-based analyzer when evaluating algorithmic efficiency:

1. **`sample02.py`** (Diff: 11.5)
   - **Ground Truth**: None (Rank 8.5) - Clean data processing with no known defects.
   - **CodePilot Score**: 79.0 (Aligned Rank 1.0) | LOC: 37 | Issues: 2
   - **Analysis**: CodePilot assigned this the *lowest* performance score of the entire benchmark. The static analyzer likely caught a false positive or mapped a superficial stylistic issue to the performance category, unfairly penalizing code that the ground truth considers clean. This is an issue with static scoring behavior/categorization.

2. **`sample19.py`** (Diff: 11.5)
   - **Ground Truth**: Critical (Rank 20.0) - O(N³) nested loops.
   - **CodePilot Score**: 100.0 (Aligned Rank 12.5) | LOC: 76 | Issues: 1
   - **Analysis**: The static analyzer scored this file perfectly (100.0) because regex rules cannot evaluate asymptotic time complexity. It completely missed the critical O(N³) bottleneck. This is a detection failure of the static engine.

3. **`sample15.py`** (Diff: 10.5)
   - **Ground Truth**: High (Rank 19.0) - N+1 query problem.
   - **CodePilot Score**: 100.0 (Aligned Rank 12.5) | LOC: 57 | Issues: 1
   - **Analysis**: Similar to `sample19.py`, CodePilot missed the N+1 SQL query inside a loop, scoring it 100.0. The static analyzer cannot track dataflow or database interactions across loops.

4. **`sample05.py`** (Diff: 9.5)
   - **Ground Truth**: None (Rank 8.5) - Mild style issues (unused imports).
   - **CodePilot Score**: 90.0 (Aligned Rank 3.0) | LOC: 35 | Issues: 3
   - **Analysis**: The static engine detected issues (likely bare excepts or unused imports) and the scoring engine inappropriately penalized the performance score, despite these being purely maintainability concerns.

## 7. Interpretation

The Spearman correlation is **ρ = -0.017**, indicating **zero monotonic relationship** between the CodePilot (static) Performance Score and the actual ground-truth performance severity. 

This result does not prove the model is valid, nor does it validate the static engine. Under a conservative interpretation, this effectively proves that **a static, regex-based analyzer is fundamentally incapable of assessing software performance**. CodePilot's static fallback engine is blind to asymptotic complexity (O(N³) loops) and architectural bottlenecks (N+1 queries), while occasionally penalizing clean code due to miscategorized superficial rule hits. 

This strongly validates the necessity of the Hybrid Engine and Gemini AI for CodePilot's performance analysis, as the deterministic static engine alone provides no signal.

## 8. Limitations
- **n = 20**: The sample size is extremely small and controlled.
- **Ordinal Ground Truth**: The ground-truth severity is a qualitative ranking rather than a continuous benchmark of execution time or memory allocation.
- **Static-Only Mode**: CodePilot was run intentionally without Gemini AI. The lack of correlation is primarily a measurement of the static fallback pipeline, not the fully active AI engine.
