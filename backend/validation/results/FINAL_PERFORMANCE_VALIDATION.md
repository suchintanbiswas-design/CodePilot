# Final Performance Validation (Unseen Holdout)

**This is an unseen holdout evaluation.** 

The dataset and labels were created after all rule tuning was completed. The ground truth was strictly determined using standard software engineering principles (Big-O notation, database access patterns) prior to inspecting CodePilot's output, ensuring complete independence. The scoring model and analyzer weights have not been modified based on these results.

## Dataset Construction & Ground-Truth Methodology
A new dataset of 15 realistic Python files (inal01.py to inal15.py) was constructed to test the generalizability of CodePilot's Performance scoring pipeline. The set includes a balanced mix of:
- Clean, efficient O(N) processing and optimal tree traversal.
- Harmless sequential loops (O(N) + O(N)).
- Genuine algorithmic inefficiency (O(N^2) and O(N^3) nested loops).
- Genuine N+1 query patterns (db.execute in a loop).
- Realistic edge cases: ORM N+1 queries, string concatenation inefficiency, list.index() inside loops, batched SQL queries, and etchone streaming.

The ground-truth performance severity (
one, low, medium, high, critical) was assigned via manual code review strictly based on theoretical algorithmic complexity and network bound anti-patterns.

## Validation Results

**Sample Size (n):** 15

### Correlation Analysis
* **Spearman rho:** -0.7890
* **p-value:** < 0.001 (t = -4.63, df = 13)

The strong negative correlation confirms that as the ground-truth performance severity increases, the CodePilot Performance Score significantly decreases. This is a dramatic improvement over the initial benchmark evaluation (which had $\rho$ = -0.017). The performance scoring engine now successfully captures algorithmic and database-related performance defects.

### Classification Behavior
When evaluating the binary classification task (Performance Issue Present vs. Not Present), CodePilot achieved the following:

* **True Positives (TP):** 5
* **False Positives (FP):** 0
* **True Negatives (TN):** 7
* **False Negatives (FN):** 3

* **Precision:** 1.0000 (100%)
* **Recall:** 0.6250 (62.5%)
* **F1 Score:** 0.7692

#### Confusion Matrix
| | CodePilot Penalty | CodePilot Perfect Score (100) |
|---|---|---|
| **Ground Truth Issue** | 5 (TP) | 3 (FN) |
| **Ground Truth Clean** | 0 (FP) | 7 (TN) |

## Interpretation & Disagreements

**100% Precision:** The static analyzer produced **zero false positives** on the unseen holdout. Harmless sequential loops, batched queries, safe etchone iteration, and unrelated .execute() command patterns were all correctly ignored by the new heuristics.

**62.5% Recall:** CodePilot successfully caught nested or loops (O(N^2) and O(N^3)) and raw SQL N+1 query patterns. As expected for a purely static heuristic analyzer without deep dataflow or type inference, it missed three specific subtle patterns:
1. inal10.py (String Concatenation): Missed s += str(i) in a loop (Expected: low).
2. inal12.py (ORM N+1 Query): Missed session.query(Profile).filter_by(...).first() inside a loop because it lacks the .execute() method name signature (Expected: high).
3. inal13.py (Repeated list lookup): Missed eference_list.index(item) inside a loop which degrades to O(N^2) runtime (Expected: medium).

## Limitations
- These results reflect the static pipeline only. The Gemini AI hybrid engine was not enabled, which could potentially detect the subtle issues (ORM patterns, list indexing) missed by the AST rules.
- The dataset is relatively small (n=15), though the p-value indicates statistical significance.
- The static AST heuristics prioritize precision over recall to prevent frustrating false positives for users, which inherently limits detection of heavily abstracted framework inefficiencies.
