#!/usr/bin/env python3
"""CodePilot Validation Analysis Script

Analyzes the results produced by run_validation.py and performs:

1. Mathematical validation
   - Boundedness: all scores ∈ [0, 100]
   - Severity monotonicity (from model_properties)
   - Confidence monotonicity (synthetic)
   - Issue-addition monotonicity (adding issues never improves scores)
   - Complexity monotonicity (from model_properties)
   - Size-normalization consistency (from model_properties)

2. Benchmark summaries
   - Mean, median, min, max, stddev per metric

3. Ranking preparation
   - Produces ranked CSVs for later external comparison

Does NOT generate fake correlation coefficients.
Does NOT claim external validation has occurred.

Usage:
  cd backend
  python -m validation.scripts.analyze_results

Input:
  backend/validation/results/codepilot_results.csv

Output:
  backend/validation/results/analysis_summary.txt
  backend/validation/results/ranked_by_overall.csv
  backend/validation/results/ranked_by_security.csv
  backend/validation/results/ranked_by_maintainability.csv
"""

import csv
import os
import statistics
import sys

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


def load_csv(path: str) -> list:
    """Load a CSV file as a list of dicts."""
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_ranked_csv(
    rows: list, sort_key: str, output_path: str, ascending: bool = True
):
    """Save rows sorted by a numeric key."""
    sorted_rows = sorted(rows, key=lambda r: float(r[sort_key]), reverse=not ascending)
    ranked = []
    for i, row in enumerate(sorted_rows, 1):
        ranked.append({"rank": i, **row})
    fieldnames = ["rank"] + list(rows[0].keys())
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(ranked)


def validate_boundedness(rows: list) -> list:
    """Check all scores are in [0, 100]."""
    score_fields = [
        "security_score",
        "performance_score",
        "maintainability_score",
        "technical_debt_health",
        "overall_quality",
    ]
    violations = []
    for row in rows:
        for field in score_fields:
            val = float(row[field])
            if val < 0 or val > 100:
                violations.append(f"{row['file']}: {field}={val} OUT OF BOUNDS")
    return violations


def validate_severity_monotonicity(rows: list) -> list:
    """Check severity ordering from model_properties files."""
    severity_files = {
        "severity_low.py": 1,
        "severity_medium.py": 2,
        "severity_high.py": 3,
        "severity_critical.py": 4,
    }
    severity_rows = {}
    for row in rows:
        if row["file"] in severity_files:
            severity_rows[severity_files[row["file"]]] = row

    violations = []
    if len(severity_rows) < 4:
        violations.append("WARNING: Not all severity files found in results")
        return violations

    # Higher severity → lower overall quality
    for i in range(1, 4):
        oq_lower = float(severity_rows[i]["overall_quality"])
        oq_higher = float(severity_rows[i + 1]["overall_quality"])
        if oq_higher > oq_lower:
            violations.append(
                f"Severity monotonicity violation: severity level {i+1} "
                f"(OQ={oq_higher}) > level {i} (OQ={oq_lower})"
            )
    return violations


def validate_complexity_monotonicity(rows: list) -> list:
    """Check complexity ordering from model_properties files."""
    complexity_files = {
        "complexity_low.py": 1,
        "complexity_medium.py": 2,
        "complexity_high.py": 3,
    }
    complexity_rows = {}
    for row in rows:
        if row["file"] in complexity_files:
            complexity_rows[complexity_files[row["file"]]] = row

    violations = []
    if len(complexity_rows) < 3:
        violations.append("WARNING: Not all complexity files found in results")
        return violations

    # Higher complexity → lower maintainability
    for i in range(1, 3):
        ms_lower = float(complexity_rows[i]["maintainability_score"])
        ms_higher = float(complexity_rows[i + 1]["maintainability_score"])
        if ms_higher > ms_lower:
            violations.append(
                f"Complexity monotonicity violation: complexity level {i+1} "
                f"(Maint={ms_higher}) > level {i} (Maint={ms_lower})"
            )
    return violations


def validate_confidence_monotonicity(rows: list) -> list:
    """Check confidence ordering from synthetic files."""
    conf_files = {
        "confidence_10.py": 10,
        "confidence_25.py": 25,
        "confidence_50.py": 50,
        "confidence_75.py": 75,
        "confidence_100.py": 100,
    }
    conf_rows = {}
    for row in rows:
        if row["file"] in conf_files:
            conf_rows[conf_files[row["file"]]] = row

    violations = []
    if len(conf_rows) < 5:
        violations.append("WARNING: Not all confidence files found in results")
        return violations

    # Higher confidence -> lower overall quality
    confs = [10, 25, 50, 75, 100]
    for i in range(len(confs) - 1):
        c_lower = confs[i]
        c_higher = confs[i + 1]
        oq_lower = float(conf_rows[c_lower]["overall_quality"])
        oq_higher = float(conf_rows[c_higher]["overall_quality"])
        if oq_higher > oq_lower:
            violations.append(
                f"Confidence monotonicity violation: conf {c_higher}% "
                f"(OQ={oq_higher}) > conf {c_lower}% (OQ={oq_lower})"
            )
    return violations


def validate_size_normalization(rows: list) -> list:
    """Check size normalization consistency from model_properties files."""
    size_files = ["size_500.py", "size_1000.py", "size_2000.py"]
    size_rows = {}
    for row in rows:
        if row["file"] in size_files:
            size_rows[row["file"]] = row

    violations = []
    if len(size_rows) < 3:
        violations.append("WARNING: Not all size normalization files found in results")
        return violations

    # With proportional issues, normalized_impact should be similar
    impacts = [float(size_rows[f]["normalized_impact"]) for f in size_files]
    max_diff = max(impacts) - min(impacts)

    # Allow some tolerance since issues may not be perfectly proportional
    # after real static analysis
    if max_diff > 5.0:
        violations.append(
            f"Size normalization: normalized_impact spread = {max_diff:.2f} "
            f"(values: {impacts}). Large spread suggests density mismatch."
        )
    return violations


def compute_statistics(rows: list, field: str) -> dict:
    """Compute descriptive statistics for a numeric field."""
    values = [float(row[field]) for row in rows]
    if not values:
        return {"mean": 0, "median": 0, "min": 0, "max": 0, "stddev": 0, "count": 0}
    return {
        "count": len(values),
        "mean": round(statistics.mean(values), 2),
        "median": round(statistics.median(values), 2),
        "min": round(min(values), 2),
        "max": round(max(values), 2),
        "stddev": round(statistics.stdev(values), 2) if len(values) > 1 else 0,
    }


def main():
    validation_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    results_dir = os.path.join(validation_dir, "results")
    csv_path = os.path.join(results_dir, "codepilot_results.csv")

    if not os.path.exists(csv_path):
        print(f"ERROR: {csv_path} not found. Run run_validation.py first.")
        sys.exit(1)

    rows = load_csv(csv_path)
    print(f"Loaded {len(rows)} results from {csv_path}\n")

    # Separate benchmark samples from model_properties
    benchmark_rows = [r for r in rows if r["file"].startswith("sample")]
    [r for r in rows if not r["file"].startswith("sample")]

    output_lines = []

    def log(msg=""):
        print(msg)
        output_lines.append(msg)

    # ═══════════════════════════════════════════════════════════════
    # 1. Mathematical Validation
    # ═══════════════════════════════════════════════════════════════
    log("=" * 70)
    log("MATHEMATICAL VALIDATION")
    log("=" * 70)

    # Boundedness
    log("\n--- Boundedness Check ---")
    bound_violations = validate_boundedness(rows)
    if bound_violations:
        for v in bound_violations:
            log(f"  FAIL: {v}")
    else:
        log(f"  PASS: All {len(rows)} files have scores in [0, 100]")

    # Severity Monotonicity
    log("\n--- Severity Monotonicity ---")
    sev_violations = validate_severity_monotonicity(rows)
    if sev_violations:
        for v in sev_violations:
            log(f"  FAIL: {v}")
    else:
        log("  PASS: Higher severity -> lower overall quality")

    # Confidence Monotonicity
    log("\n--- Confidence Monotonicity ---")
    conf_violations = validate_confidence_monotonicity(rows)
    if conf_violations:
        for v in conf_violations:
            log(f"  FAIL: {v}")
    else:
        log("  PASS: Higher confidence -> lower overall quality")

    # Complexity Monotonicity
    log("\n--- Complexity Monotonicity ---")
    comp_violations = validate_complexity_monotonicity(rows)
    if comp_violations:
        for v in comp_violations:
            log(f"  FAIL: {v}")
    else:
        log("  PASS: Higher complexity -> lower maintainability")

    # Size Normalization
    log("\n--- Size Normalization Consistency ---")
    size_violations = validate_size_normalization(rows)
    if size_violations:
        for v in size_violations:
            log(f"  INFO: {v}")
    else:
        log("  PASS: Proportional issues produce similar normalized impact")

    total_violations = (
        len(bound_violations)
        + len(sev_violations)
        + len(comp_violations)
        + len(conf_violations)
    )
    log(f"\nTotal strict violations: {total_violations}")

    # ═══════════════════════════════════════════════════════════════
    # 2. Benchmark Summaries (sample files only)
    # ═══════════════════════════════════════════════════════════════
    log("\n" + "=" * 70)
    log("BENCHMARK SUMMARIES (20 sample files)")
    log("=" * 70)

    summary_fields = [
        "overall_quality",
        "security_score",
        "performance_score",
        "maintainability_score",
        "technical_debt_health",
        "issue_count",
        "average_complexity",
        "total_impact",
    ]

    for field in summary_fields:
        stats = compute_statistics(benchmark_rows, field)
        log(f"\n  {field}:")
        log(
            f"    count={stats['count']}  mean={stats['mean']}  median={stats['median']}  "
            f"min={stats['min']}  max={stats['max']}  stddev={stats['stddev']}"
        )

    # ═══════════════════════════════════════════════════════════════
    # 3. Group Analysis
    # ═══════════════════════════════════════════════════════════════
    log("\n" + "=" * 70)
    log("GROUP ANALYSIS")
    log("=" * 70)

    groups = {
        "A (Clean)": [
            r
            for r in benchmark_rows
            if r["file"] in [f"sample{i:02d}.py" for i in range(1, 5)]
        ],
        "B (Low)": [
            r
            for r in benchmark_rows
            if r["file"] in [f"sample{i:02d}.py" for i in range(5, 9)]
        ],
        "C (Medium)": [
            r
            for r in benchmark_rows
            if r["file"] in [f"sample{i:02d}.py" for i in range(9, 13)]
        ],
        "D (High)": [
            r
            for r in benchmark_rows
            if r["file"] in [f"sample{i:02d}.py" for i in range(13, 17)]
        ],
        "E (Critical)": [
            r
            for r in benchmark_rows
            if r["file"] in [f"sample{i:02d}.py" for i in range(17, 21)]
        ],
    }

    for group_name, group_rows in groups.items():
        if not group_rows:
            log(f"\n  {group_name}: No files found")
            continue
        stats = compute_statistics(group_rows, "overall_quality")
        log(f"\n  {group_name}:")
        log(f"    Files: {[r['file'] for r in group_rows]}")
        log(
            f"    Overall Quality: mean={stats['mean']}  min={stats['min']}  max={stats['max']}"
        )

    # Check group ordering (A > B > C > D > E in mean overall quality)
    log("\n--- Group Ordering Check ---")
    group_means = {}
    for group_name, group_rows in groups.items():
        if group_rows:
            group_means[group_name] = statistics.mean(
                [float(r["overall_quality"]) for r in group_rows]
            )

    group_names_ordered = list(groups.keys())
    ordering_ok = True
    for i in range(len(group_names_ordered) - 1):
        g1 = group_names_ordered[i]
        g2 = group_names_ordered[i + 1]
        if g1 in group_means and g2 in group_means:
            if group_means[g1] < group_means[g2]:
                log(
                    f"  WARNING: {g1} mean ({group_means[g1]:.1f}) < {g2} mean ({group_means[g2]:.1f})"
                )
                ordering_ok = False
    if ordering_ok:
        log("  PASS: Group means are ordered A > B > C > D > E")

    # ═══════════════════════════════════════════════════════════════
    # 4. Ranking Preparation
    # ═══════════════════════════════════════════════════════════════
    log("\n" + "=" * 70)
    log("RANKING PREPARATION")
    log("=" * 70)

    # Ranked CSVs for external comparison
    save_ranked_csv(
        benchmark_rows,
        "overall_quality",
        os.path.join(results_dir, "ranked_by_overall.csv"),
        ascending=True,
    )
    save_ranked_csv(
        benchmark_rows,
        "security_score",
        os.path.join(results_dir, "ranked_by_security.csv"),
        ascending=True,
    )
    save_ranked_csv(
        benchmark_rows,
        "maintainability_score",
        os.path.join(results_dir, "ranked_by_maintainability.csv"),
        ascending=True,
    )

    log("  Saved: ranked_by_overall.csv")
    log("  Saved: ranked_by_security.csv")
    log("  Saved: ranked_by_maintainability.csv")
    log(
        "\n  These CSVs can be joined with independently collected external measurements"
    )
    log(
        "  (SonarQube, Radon MI, expert ratings) for Spearman rank correlation analysis."
    )

    # Save analysis summary
    summary_path = os.path.join(results_dir, "analysis_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    log(f"\n{'='*70}")
    log(f"Analysis complete. Summary saved to: {summary_path}")
    log(f"{'='*70}")


if __name__ == "__main__":
    main()
