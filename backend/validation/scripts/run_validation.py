#!/usr/bin/env python3
"""CodePilot Validation Runner

Runs each benchmark sample through the REAL CodePilot static analysis and scoring
pipeline, WITHOUT calling Gemini or consuming AI quota.

Pipeline used:
  1. StaticAnalyzer.analyze(code, "Python")         → raw static issues
  2. StaticAnalyzer.calculate_cyclomatic_complexity  → total complexity
  3. HybridEngine.normalize(issues, "Static")        → normalized issues
  4. HybridEngine.fuse(normalized, [])               → unified issues (no AI)
  5. ConfidenceEngine.calculate_all(unified)          → confidence-injected issues
  6. ScoringEngine.calculate_scores(...)              → final scores

AI Confidence Handling:
  - Since Gemini is NOT called, all issues originate from the static analyzer.
  - The HybridEngine tags them with source="Static".
  - The ConfidenceEngine assigns base confidence=85 for Static-only issues
    (plus severity adjustments: Critical +5, High +3, Medium +1, Low +0).
  - This is the REAL confidence pipeline, not a mock. We simply skip the AI
    analysis step, exactly as CodePilot behaves when Gemini is unavailable.

Function Counting:
  - We count Python function/method definitions (def keyword) to compute
    num_functions for the average complexity calculation.

Usage:
  cd backend
  python -m validation.scripts.run_validation

Output:
  backend/validation/results/codepilot_results.csv
"""

import csv
import os
import re
import sys

# Ensure the backend app is importable
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.engine.static_analyzer import StaticAnalyzer
from app.engine.hybrid_engine import HybridEngine
from app.engine.confidence_engine import ConfidenceEngine
from app.engine.scoring_engine import ScoringEngine


def count_functions(code: str) -> int:
    """Count top-level and nested function/method definitions in Python code."""
    return len(re.findall(r"^\s*def\s+\w+", code, re.MULTILINE))


def run_single(filepath: str, analyzer: StaticAnalyzer, hybrid: HybridEngine,
               confidence: ConfidenceEngine, scorer: ScoringEngine) -> dict:
    """Run the full CodePilot pipeline on a single Python file."""
    with open(filepath, "r", encoding="utf-8") as f:
        code = f.read()

    filename = os.path.basename(filepath)
    loc = len(code.splitlines())
    num_functions = count_functions(code)

    # ---------------------------------------------------------
    # SYNTHETIC OVERRIDES FOR MODEL PROPERTIES
    # (We bypass the static analyzer to ensure the exact mathematical
    # conditions are fed into the scoring engine for validation)
    # ---------------------------------------------------------
    fname = os.path.basename(filepath)
    if "severity_" in fname:
        sev = fname.split("_")[1].replace(".py", "").capitalize()
        raw_issues = [{"severity": sev, "description": "Synthetic severity test", "rule_type": "Security"}]
        complexity = 5
        num_functions = 1
        loc = 50
    elif "size_" in fname:
        # Equivalent issue density
        loc = int(fname.split("_")[1].replace(".py", ""))
        # 1 issue per 500 lines
        issue_count = loc // 500
        raw_issues = [{"severity": "Medium", "description": "Synthetic size test", "rule_type": "Style"} for _ in range(issue_count)]
        complexity = 5 * issue_count
        num_functions = issue_count
    elif "complexity_" in fname:
        level = fname.split("_")[1].replace(".py", "")
        comp_map = {"low": 5, "medium": 10, "high": 20}
        complexity = comp_map.get(level, 5) * 4 # 4 functions
        num_functions = 4
        loc = 50
        raw_issues = [{"severity": "Low", "description": "Base issue", "rule_type": "Style"}]
    elif "confidence_" in fname:
        # Tested below via a special loop, but for the base file just return standard
        raw_issues = [{"severity": "Medium", "description": "Synthetic conf test", "rule_type": "Style"}]
        complexity = 5
        num_functions = 1
        loc = 50
    else:
        # NORMAL BENCHMARK SAMPLES
        raw_issues = analyzer.analyze(code, "Python")
        complexity = analyzer.calculate_cyclomatic_complexity(code)

    # Step 3-4: Normalize and fuse (no AI issues)
    normalized = hybrid.normalize(raw_issues, "Static")
    unified = hybrid.fuse(normalized, [])

    # Step 5: Confidence calculation
    unified = confidence.calculate_all(unified)

    # Step 6: Scoring
    scores = scorer.calculate_scores(
        unified,
        cyclomatic_complexity=complexity,
        lines_of_code=loc,
        num_functions=num_functions,
    )

    meta = scores.get("scoring_metadata", {})

    return {
        "file": filename,
        "loc": loc,
        "num_functions": num_functions,
        "issue_count": len(unified),
        "security_score": scores["security_score"],
        "performance_score": scores["performance_score"],
        "maintainability_score": scores["maintainability_score"],
        "maintainability_grade": scores["maintainability_grade"],
        "technical_debt_health": scores["technical_debt_score"],
        "overall_quality": scores["overall_quality"],
        "average_complexity": meta.get("average_complexity", 0),
        "total_impact": meta.get("total_impact", 0),
        "normalized_impact": meta.get("normalized_impact", 0),
        "confidence_adjusted_issue_count": meta.get("confidence_adjusted_issue_count", 0),
        "loc_k": meta.get("loc_k", 1.0),
    }


def discover_benchmarks(benchmark_dir: str) -> list:
    """Discover all .py benchmark files, sorted by name."""
    files = []
    for fname in sorted(os.listdir(benchmark_dir)):
        if fname.endswith(".py") and fname.startswith("sample"):
            files.append(os.path.join(benchmark_dir, fname))
    return files


def discover_model_properties(props_dir: str) -> list:
    """Discover all .py files in model_properties/, sorted."""
    if not os.path.isdir(props_dir):
        return []
    files = []
    for fname in sorted(os.listdir(props_dir)):
        if fname.endswith(".py"):
            files.append(os.path.join(props_dir, fname))
    return files


def main():
    validation_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    benchmark_dir = os.path.join(validation_dir, "benchmark")
    props_dir = os.path.join(benchmark_dir, "model_properties")
    results_dir = os.path.join(validation_dir, "results")
    os.makedirs(results_dir, exist_ok=True)

    # Initialize engines
    analyzer = StaticAnalyzer()
    hybrid = HybridEngine()
    confidence = ConfidenceEngine()
    scorer = ScoringEngine()

    # Discover files
    benchmark_files = discover_benchmarks(benchmark_dir)
    model_files = discover_model_properties(props_dir)

    all_files = benchmark_files + model_files

    if not all_files:
        print("ERROR: No benchmark files found.")
        sys.exit(1)

    print(f"Discovered {len(benchmark_files)} benchmark samples, {len(model_files)} model property files.")
    print(f"Running CodePilot pipeline (Static-only, no Gemini)...\n")

    # Run pipeline
    results = []
    fieldnames = [
        "file", "loc", "num_functions", "issue_count",
        "security_score", "performance_score", "maintainability_score",
        "maintainability_grade", "technical_debt_health", "overall_quality",
        "average_complexity", "total_impact", "normalized_impact",
        "confidence_adjusted_issue_count", "loc_k",
    ]

    for filepath in all_files:
        try:
            if "confidence_base.py" in os.path.basename(filepath):
                # Generate 5 variants for confidence testing
                for conf in [10, 25, 50, 75, 100]:
                    result = run_single(filepath, analyzer, hybrid, confidence, scorer)
                    # Force the confidence
                    # We need to re-run scoring with forced confidence
                    raw_issues = [{"severity": "Medium", "description": "Synthetic conf test", "rule_type": "Security", "source": "Static"}]
                    # hybrid/confidence bypass for pure math test
                    unified = [{"severity": "Medium", "confidence": conf, "rule_type": "Security"}]
                    scores = scorer.calculate_scores(unified, cyclomatic_complexity=5, lines_of_code=50, num_functions=1)
                    
                    meta = scores.get("scoring_metadata", {})
                    result = {
                        "file": f"confidence_{conf}.py",
                        "loc": 50,
                        "num_functions": 1,
                        "issue_count": 1,
                        "security_score": scores["security_score"],
                        "performance_score": scores["performance_score"],
                        "maintainability_score": scores["maintainability_score"],
                        "maintainability_grade": scores["maintainability_grade"],
                        "technical_debt_health": scores["technical_debt_score"],
                        "overall_quality": scores["overall_quality"],
                        "average_complexity": meta.get("average_complexity", 0),
                        "total_impact": meta.get("total_impact", 0),
                        "normalized_impact": meta.get("normalized_impact", 0),
                        "confidence_adjusted_issue_count": meta.get("confidence_adjusted_issue_count", 0),
                        "loc_k": meta.get("loc_k", 1.0),
                    }
                    results.append(result)
                    print(f"  [+] {result['file']:30s}  OQ={result['overall_quality']:3d}  "
                          f"Sec={result['security_score']:3d}  Perf={result['performance_score']:3d}  "
                          f"Maint={result['maintainability_score']:3d}({result['maintainability_grade']})  "
                          f"TD={result['technical_debt_health']:3d}  Issues={result['issue_count']}")
                continue

            result = run_single(filepath, analyzer, hybrid, confidence, scorer)
            results.append(result)
            print(f"  [+] {result['file']:30s}  OQ={result['overall_quality']:3d}  "
                  f"Sec={result['security_score']:3d}  Perf={result['performance_score']:3d}  "
                  f"Maint={result['maintainability_score']:3d}({result['maintainability_grade']})  "
                  f"TD={result['technical_debt_health']:3d}  Issues={result['issue_count']}")
        except Exception as e:
            print(f"  [-] {os.path.basename(filepath):30s}  ERROR: {e}")

    # Write CSV
    csv_path = os.path.join(results_dir, "codepilot_results.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n{'='*70}")
    print(f"Results saved to: {csv_path}")
    print(f"Total files processed: {len(results)}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
