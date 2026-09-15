# Performance Holdout Dataset

This directory contains a holdout dataset designed specifically for the unbiased external validation of CodePilot's performance scoring.

## Important Constraints
- **This is a holdout set:** It must NOT be used for tuning rules, adjusting weights, or modifying analyzer heuristics.
- **Created after rule changes:** This dataset was assembled *after* the PY_NESTED_LOOP_COMPLEXITY and PY_N_PLUS_1_QUERY rules were implemented, to verify their generalizability.
- **Independent ground truth:** The labels in performance_ground_truth.csv were determined by standard software engineering principles (Big-O analysis, database patterns) completely independent of CodePilot's output or rule implementations.

## Contents
- performance/: Contains 10 Python files (holdout01.py through holdout10.py).
- performance_ground_truth.csv: Contains the ordinal performance labels (
one, low, medium, high, critical) and the rationale for each file.
