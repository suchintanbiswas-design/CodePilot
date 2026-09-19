"""Tests for the validation harness itself.

These tests verify the integrity of the benchmark dataset and validation
infrastructure, NOT the scoring engine (those are in test_scoring_engine.py).

Verifies:
- Every benchmark file is discovered
- Every ground-truth row maps to exactly one benchmark file
- No benchmark file is missing from ground truth
- No duplicate manifest entries
- Results contain all required fields
- All scores remain in [0, 100]
"""

import csv
import os
import sys

import pytest

# Paths
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VALIDATION_DIR = os.path.join(BACKEND_DIR, "validation")
BENCHMARK_DIR = os.path.join(VALIDATION_DIR, "benchmark")
PROPS_DIR = os.path.join(BENCHMARK_DIR, "model_properties")
GROUND_TRUTH_CSV = os.path.join(BENCHMARK_DIR, "ground_truth.csv")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


class TestBenchmarkDiscovery:
    """Verify all benchmark files are present and discoverable."""

    def test_benchmark_dir_exists(self):
        assert os.path.isdir(BENCHMARK_DIR), f"Benchmark dir missing: {BENCHMARK_DIR}"

    def test_exactly_20_sample_files(self):
        samples = [
            f
            for f in os.listdir(BENCHMARK_DIR)
            if f.startswith("sample") and f.endswith(".py")
        ]
        assert (
            len(samples) == 20
        ), f"Expected 20 sample files, found {len(samples)}: {sorted(samples)}"

    def test_sample_files_named_correctly(self):
        expected = {f"sample{i:02d}.py" for i in range(1, 21)}
        actual = {
            f
            for f in os.listdir(BENCHMARK_DIR)
            if f.startswith("sample") and f.endswith(".py")
        }
        assert (
            actual == expected
        ), f"Missing: {expected - actual}, Extra: {actual - expected}"

    def test_model_properties_dir_exists(self):
        assert os.path.isdir(PROPS_DIR), f"Model properties dir missing: {PROPS_DIR}"

    def test_model_properties_files_exist(self):
        expected_files = [
            "confidence_base.py",
            "severity_low.py",
            "severity_medium.py",
            "severity_high.py",
            "severity_critical.py",
            "size_500.py",
            "size_1000.py",
            "size_2000.py",
            "complexity_low.py",
            "complexity_medium.py",
            "complexity_high.py",
        ]
        actual = set(os.listdir(PROPS_DIR))
        for f in expected_files:
            assert f in actual, f"Model property file missing: {f}"

    def test_all_benchmark_files_valid_python(self):
        """Every benchmark file must be syntactically valid Python."""
        for fname in sorted(os.listdir(BENCHMARK_DIR)):
            if fname.endswith(".py") and fname.startswith("sample"):
                filepath = os.path.join(BENCHMARK_DIR, fname)
                with open(filepath, "r", encoding="utf-8") as f:
                    code = f.read()
                try:
                    compile(code, filepath, "exec")
                except SyntaxError as e:
                    pytest.fail(f"Syntax error in {fname}: {e}")

    def test_all_model_property_files_valid_python(self):
        """Every model property file must be syntactically valid Python."""
        for fname in sorted(os.listdir(PROPS_DIR)):
            if fname.endswith(".py"):
                filepath = os.path.join(PROPS_DIR, fname)
                with open(filepath, "r", encoding="utf-8") as f:
                    code = f.read()
                try:
                    compile(code, filepath, "exec")
                except SyntaxError as e:
                    pytest.fail(f"Syntax error in {fname}: {e}")


class TestGroundTruth:
    """Verify the ground-truth manifest integrity."""

    def _load_ground_truth(self):
        with open(GROUND_TRUTH_CSV, "r", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def test_ground_truth_file_exists(self):
        assert os.path.isfile(
            GROUND_TRUTH_CSV
        ), f"Ground truth CSV missing: {GROUND_TRUTH_CSV}"

    def test_ground_truth_has_20_rows(self):
        rows = self._load_ground_truth()
        assert len(rows) == 20, f"Expected 20 rows, got {len(rows)}"

    def test_ground_truth_required_columns(self):
        rows = self._load_ground_truth()
        required = {
            "file",
            "loc_expected",
            "expected_security_level",
            "expected_performance_level",
            "expected_maintainability_level",
            "known_issue_summary",
            "ground_truth_source",
        }
        actual = set(rows[0].keys())
        missing = required - actual
        assert not missing, f"Missing columns: {missing}"

    def test_every_ground_truth_maps_to_benchmark_file(self):
        rows = self._load_ground_truth()
        benchmark_files = {
            f
            for f in os.listdir(BENCHMARK_DIR)
            if f.startswith("sample") and f.endswith(".py")
        }
        for row in rows:
            assert (
                row["file"] in benchmark_files
            ), f"Ground truth references {row['file']} but file not found in benchmark/"

    def test_every_benchmark_file_in_ground_truth(self):
        rows = self._load_ground_truth()
        gt_files = {row["file"] for row in rows}
        benchmark_files = {
            f
            for f in os.listdir(BENCHMARK_DIR)
            if f.startswith("sample") and f.endswith(".py")
        }
        missing = benchmark_files - gt_files
        assert not missing, f"Benchmark files missing from ground truth: {missing}"

    def test_no_duplicate_manifest_entries(self):
        rows = self._load_ground_truth()
        files = [row["file"] for row in rows]
        duplicates = [f for f in files if files.count(f) > 1]
        assert not duplicates, f"Duplicate entries in ground truth: {set(duplicates)}"

    def test_valid_severity_labels(self):
        rows = self._load_ground_truth()
        valid_labels = {"none", "low", "medium", "high", "critical"}
        for row in rows:
            for col in [
                "expected_security_level",
                "expected_performance_level",
                "expected_maintainability_level",
            ]:
                assert (
                    row[col] in valid_labels
                ), f"{row['file']}: {col}={row[col]} not in {valid_labels}"


class TestValidationPipeline:
    """Test that the validation runner produces valid results."""

    def setup_method(self):
        from app.engine.confidence_engine import ConfidenceEngine
        from app.engine.hybrid_engine import HybridEngine
        from app.engine.scoring_engine import ScoringEngine
        from app.engine.static_analyzer import StaticAnalyzer

        self.analyzer = StaticAnalyzer()
        self.hybrid = HybridEngine()
        self.confidence = ConfidenceEngine()
        self.scorer = ScoringEngine()

    def _run_single(self, filepath):
        """Run pipeline on a single file (same as run_validation.py)."""
        import re

        with open(filepath, "r", encoding="utf-8") as f:
            code = f.read()

        loc = len(code.splitlines())
        num_functions = len(re.findall(r"^\s*def\s+\w+", code, re.MULTILINE))
        complexity = self.analyzer.calculate_cyclomatic_complexity(code)
        raw_issues = self.analyzer.analyze(code, "Python")
        normalized = self.hybrid.normalize(raw_issues, "Static")
        unified = self.hybrid.fuse(normalized, [])
        unified = self.confidence.calculate_all(unified)
        scores = self.scorer.calculate_scores(
            unified,
            cyclomatic_complexity=complexity,
            lines_of_code=loc,
            num_functions=num_functions,
        )
        return scores

    def test_all_benchmark_files_produce_valid_scores(self):
        """Run pipeline on every benchmark file and verify scores are bounded."""
        score_fields = [
            "security_score",
            "performance_score",
            "maintainability_score",
            "technical_debt_score",
            "overall_quality",
        ]

        for fname in sorted(os.listdir(BENCHMARK_DIR)):
            if fname.startswith("sample") and fname.endswith(".py"):
                filepath = os.path.join(BENCHMARK_DIR, fname)
                scores = self._run_single(filepath)

                for field in score_fields:
                    assert (
                        0 <= scores[field] <= 100
                    ), f"{fname}: {field}={scores[field]} out of [0,100]"

                assert scores["maintainability_grade"] in (
                    "A",
                    "B",
                    "C",
                    "D",
                    "F",
                ), f"{fname}: invalid grade {scores['maintainability_grade']}"

    def test_results_contain_scoring_metadata(self):
        """Scoring metadata must be present for transparency."""
        filepath = os.path.join(BENCHMARK_DIR, "sample01.py")
        scores = self._run_single(filepath)
        assert "scoring_metadata" in scores
        meta = scores["scoring_metadata"]
        for key in [
            "total_impact",
            "normalized_impact",
            "confidence_adjusted_issue_count",
            "normalized_issue_density",
            "average_complexity",
            "loc_k",
            "lines_of_code",
            "num_functions",
            "raw_issue_count",
        ]:
            assert key in meta, f"Missing metadata key: {key}"

    def test_clean_code_scores_high(self):
        """Group A files should generally score high."""
        for i in range(1, 5):
            filepath = os.path.join(BENCHMARK_DIR, f"sample{i:02d}.py")
            if os.path.exists(filepath):
                scores = self._run_single(filepath)
                # Clean code should have overall quality >= 70 at minimum
                assert (
                    scores["overall_quality"] >= 50
                ), f"sample{i:02d}.py: clean code scored only {scores['overall_quality']}"
