#!/usr/bin/env python3
"""Diagnostic: dump all CodePilot findings per benchmark file with category classification."""

import os
import re
import sys

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.engine.confidence_engine import ConfidenceEngine
from app.engine.hybrid_engine import HybridEngine
from app.engine.scoring_engine import ScoringEngine
from app.engine.static_analyzer import StaticAnalyzer

PERFORMANCE_KEYWORDS = frozenset(
    {
        "performance",
        "complexity",
        "inefficient",
        "loop",
        "algorithm",
        "resource",
    }
)
SECURITY_KEYWORDS = frozenset(
    {
        "security",
        "secret",
        "password",
        "credential",
        "injection",
        "authentication",
        "authorization",
        "eval",
        "unsafe",
    }
)


def count_functions(code: str) -> int:
    return len(re.findall(r"^\s*def\s+\w+", code, re.MULTILINE))


def classify_issue(issue):
    rule_type = str(issue.get("rule_type", "")).lower()
    description = str(issue.get("description", "")).lower()
    text = f"{rule_type} {description}"

    cats = []
    if any(kw in text for kw in SECURITY_KEYWORDS):
        cats.append("Security")
    if any(kw in text for kw in PERFORMANCE_KEYWORDS):
        cats.append("Performance")
    if not cats:
        cats.append("Other")
    return cats


def main():
    validation_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    benchmark_dir = os.path.join(validation_dir, "benchmark")

    analyzer = StaticAnalyzer()
    hybrid = HybridEngine()
    confidence = ConfidenceEngine()
    scorer = ScoringEngine()

    for i in range(1, 21):
        fname = f"sample{i:02d}.py"
        filepath = os.path.join(benchmark_dir, fname)

        with open(filepath, "r", encoding="utf-8") as f:
            code = f.read()

        loc = len(code.splitlines())
        num_functions = count_functions(code)
        raw_issues = analyzer.analyze(code, "Python")
        complexity = analyzer.calculate_cyclomatic_complexity(code)

        normalized = hybrid.normalize(raw_issues, "Static")
        unified = hybrid.fuse(normalized, [])
        unified = confidence.calculate_all(unified)

        scores = scorer.calculate_scores(
            unified,
            cyclomatic_complexity=complexity,
            lines_of_code=loc,
            num_functions=num_functions,
        )

        meta = scores.get("scoring_metadata", {})

        # Calculate performance_impact manually
        perf_impact = 0.0
        sec_impact = 0.0
        for issue in unified:
            severity = str(issue.get("severity", "Low")).lower()
            weight = {"critical": 10, "high": 7, "medium": 4, "low": 1}.get(severity, 1)
            conf = float(issue.get("confidence", 50))
            impact = weight * (conf / 100.0)

            rule_type = str(issue.get("rule_type", "")).lower()
            desc = str(issue.get("description", "")).lower()
            text = f"{rule_type} {desc}"

            if any(kw in text for kw in PERFORMANCE_KEYWORDS):
                perf_impact += impact
            if any(kw in text for kw in SECURITY_KEYWORDS):
                sec_impact += impact

        perf_penalty = 3.0 * perf_impact
        max(0, min(100, 100.0 - perf_penalty))

        print(f"{'='*80}")
        print(f"FILE: {fname}")
        print(f"  LOC: {loc}, Functions: {num_functions}, Complexity: {complexity}")
        print(f"  Avg Complexity: {meta.get('average_complexity', 0):.2f}")
        print(f"  Issues: {len(unified)}")
        print(
            f"  Security Score: {scores['security_score']}, Performance Score: {scores['performance_score']}"
        )
        print(f"  Maintainability Score: {scores['maintainability_score']}")
        print(
            f"  Performance Impact: {perf_impact:.4f}, Performance Penalty: {perf_penalty:.4f}"
        )
        print(f"  Security Impact: {sec_impact:.4f}")
        print()

        if unified:
            for idx, issue in enumerate(unified):
                cats = classify_issue(issue)
                print(f"  Issue #{idx+1}:")
                print(f"    rule_type:   {issue.get('rule_type', 'N/A')}")
                print(f"    severity:    {issue.get('severity', 'N/A')}")
                print(f"    confidence:  {issue.get('confidence', 'N/A')}")
                print(f"    description: {issue.get('description', 'N/A')}")
                print(f"    categories:  {', '.join(cats)}")

                sev = str(issue.get("severity", "Low")).lower()
                w = {"critical": 10, "high": 7, "medium": 4, "low": 1}.get(sev, 1)
                c = float(issue.get("confidence", 50))
                print(f"    impact:      {w * c / 100:.4f}")
                print()
        else:
            print("  (no issues detected)")
            print()


if __name__ == "__main__":
    main()
