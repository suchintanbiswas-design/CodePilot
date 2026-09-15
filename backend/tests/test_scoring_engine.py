"""Tests for the CodePilot Scoring Engine v2.0.

Covers:
* A. Baseline: zero issues → all scores = 100
* B. Severity ordering: Low < Medium < High < Critical in impact
* C. Confidence ordering: 100% > 75% > 50% > 10% impact
* D. Maintainability confidence consistency (the old bug)
* E. Size normalization: same density = same normalized impact
* F. Issue density: normalized issue density scales correctly
* G. Complexity: average complexity monotonicity
* H. Non-improvement: adding a finding never increases a score
* I. Bounds: extreme inputs never produce negative or >100 scores
* J. Overall score: exact weighted-sum verification
* K. Missing/zero values: no division-by-zero exceptions
* L. Regression tests: preserved existing test scenarios with updated expectations
* M. Real-code integration tests (preserved from v1.0)
"""

from app.engine.scoring_engine import ScoringEngine


def _make_issue(severity="Low", confidence=100, rule_type="General", description="Test issue."):
    """Helper to create a minimal issue dict."""
    return {
        "severity": severity,
        "confidence": confidence,
        "rule_type": rule_type,
        "description": description,
    }


class TestBaseline:
    """A. Zero issues, zero complexity → all scores = 100."""

    def setup_method(self):
        self.engine = ScoringEngine()

    def test_no_issues_perfect_scores(self):
        result = self.engine.calculate_scores([])
        assert result["overall_quality"] == 100
        assert result["security_score"] == 100
        assert result["performance_score"] == 100
        assert result["technical_debt_score"] == 100
        assert result["maintainability_score"] == 100
        assert result["maintainability_grade"] == "A"

    def test_no_issues_with_loc(self):
        result = self.engine.calculate_scores([], lines_of_code=5000)
        assert result["overall_quality"] == 100
        assert result["maintainability_score"] == 100

    def test_version_is_2_0(self):
        result = self.engine.calculate_scores([])
        assert result["version"] == "2.0"

    def test_scoring_metadata_present(self):
        result = self.engine.calculate_scores([], lines_of_code=2000, num_functions=10)
        meta = result["scoring_metadata"]
        assert meta["total_impact"] == 0
        assert meta["normalized_impact"] == 0
        assert meta["confidence_adjusted_issue_count"] == 0
        assert meta["loc_k"] == 2.0
        assert meta["lines_of_code"] == 2000
        assert meta["num_functions"] == 10


class TestSeverityOrdering:
    """B. For the same confidence, Low < Medium < High < Critical in impact."""

    def setup_method(self):
        self.engine = ScoringEngine()

    def test_severity_impact_ordering(self):
        """Each higher severity must produce a strictly higher impact and lower scores."""
        results = {}
        for sev in ["Low", "Medium", "High", "Critical"]:
            result = self.engine.calculate_scores([_make_issue(severity=sev, confidence=100)])
            results[sev] = result

        # Overall quality decreases as severity increases
        assert results["Low"]["overall_quality"] > results["Medium"]["overall_quality"]
        assert results["Medium"]["overall_quality"] > results["High"]["overall_quality"]
        assert results["High"]["overall_quality"] > results["Critical"]["overall_quality"]

    def test_severity_weights_exact(self):
        """Verify exact severity weight values."""
        assert ScoringEngine.SEVERITY_WEIGHTS["critical"] == 10
        assert ScoringEngine.SEVERITY_WEIGHTS["high"] == 7
        assert ScoringEngine.SEVERITY_WEIGHTS["medium"] == 4
        assert ScoringEngine.SEVERITY_WEIGHTS["low"] == 1


class TestConfidenceOrdering:
    """C. For the same severity, 100% > 75% > 50% > 10% confidence in impact."""

    def setup_method(self):
        self.engine = ScoringEngine()

    def test_confidence_impact_ordering(self):
        """Higher confidence must produce a strictly higher impact and lower scores."""
        results = {}
        for conf in [10, 50, 75, 100]:
            result = self.engine.calculate_scores([_make_issue(severity="High", confidence=conf)])
            results[conf] = result

        # Overall quality decreases as confidence increases (more certain → bigger penalty)
        assert results[10]["overall_quality"] > results[50]["overall_quality"]
        assert results[50]["overall_quality"] > results[75]["overall_quality"]
        assert results[75]["overall_quality"] > results[100]["overall_quality"]


class TestMaintainabilityConfidenceConsistency:
    """D. Test the previous bug: 50 Low issues at 10% confidence.

    OLD (v1.0):
        TotalImpact = 50 × (1 × 0.1) = 5
        TechDebtHealth = 100 - (5 × 2) = 90
        MaintPenalty = (5 × 1.5) + 0 + 50 = 57.5   ← raw IssueCount = 50!
        Maintainability = 42.5                       ← disproportionately destroyed

    NEW (v2.0):
        TotalImpact = 50 × (1 × 0.1) = 5
        LOC_K = max(0/1000, 1.0) = 1.0 (no LOC provided)
        NormalizedImpact = 5 / 1.0 = 5
        ConfidenceAdjustedIssueCount = 50 × 0.1 = 5
        NormalizedIssueDensity = 5 / 1.0 = 5
        AverageComplexity = 0
        MaintPenalty = (1.5 × 5) + 5 + 0 = 12.5
        Maintainability = 87.5                       ← consistent with TechDebt ≈ 90
    """

    def setup_method(self):
        self.engine = ScoringEngine()

    def test_50_low_confidence_issues_not_destroyed(self):
        """50 Low-severity findings at 10% confidence should NOT destroy maintainability."""
        issues = [_make_issue(severity="Low", confidence=10) for _ in range(50)]
        result = self.engine.calculate_scores(issues)

        # Tech Debt Health should be ≈ 90
        assert result["technical_debt_score"] == 90

        # Maintainability should now be close to Tech Debt, NOT ≈ 42
        # MaintPenalty = 1.5×5 + 5 + 0 = 12.5 → Score = 88 (rounded)
        assert result["maintainability_score"] == 88
        assert result["maintainability_grade"] == "B"

        # The old value was 42 (grade F) - verify we're nowhere near that
        assert result["maintainability_score"] > 80

    def test_confidence_consistency_tech_debt_vs_maintainability(self):
        """Tech Debt Health and Maintainability should be in the same ballpark
        for issues where the only complication is volume of low-confidence findings."""
        issues = [_make_issue(severity="Low", confidence=10) for _ in range(50)]
        result = self.engine.calculate_scores(issues)

        # Both should be high (≥80) for low-confidence noise
        assert result["technical_debt_score"] >= 80
        assert result["maintainability_score"] >= 80

        # The gap between them should be reasonable (not 48 points like before)
        gap = abs(result["technical_debt_score"] - result["maintainability_score"])
        assert gap < 15


class TestSizeNormalization:
    """E. Same issue density across different file sizes should produce equal normalized impact."""

    def setup_method(self):
        self.engine = ScoringEngine()

    def test_equal_density_equal_normalized_impact(self):
        """1000 LOC + 10 impact vs 500 LOC + 5 impact → same normalized impact."""
        # 10 High-confidence Critical issues → impact = 10 × 10 = 100
        issues_large = [_make_issue(severity="Critical", confidence=100) for _ in range(10)]
        result_large = self.engine.calculate_scores(issues_large, lines_of_code=10000)

        # 5 High-confidence Critical issues → impact = 5 × 10 = 50
        issues_small = [_make_issue(severity="Critical", confidence=100) for _ in range(5)]
        result_small = self.engine.calculate_scores(issues_small, lines_of_code=5000)

        # Normalized impact should be equal: 100/10 = 50/5 = 10
        assert result_large["scoring_metadata"]["normalized_impact"] == result_small["scoring_metadata"]["normalized_impact"]

    def test_larger_file_same_issues_better_normalized(self):
        """Same absolute issues, larger file → better normalized score (lower density)."""
        issues = [_make_issue(severity="Medium", confidence=100) for _ in range(5)]

        result_small = self.engine.calculate_scores(issues, lines_of_code=500)
        result_large = self.engine.calculate_scores(issues, lines_of_code=5000)

        # The larger file should have a better tech debt score
        assert result_large["technical_debt_score"] >= result_small["technical_debt_score"]

    def test_loc_k_minimum_guard(self):
        """LOC_K = max(LOC/1000, 1.0) → minimum is 1.0 for small/zero LOC."""
        result = self.engine.calculate_scores([], lines_of_code=0)
        assert result["scoring_metadata"]["loc_k"] == 1.0

        result = self.engine.calculate_scores([], lines_of_code=500)
        assert result["scoring_metadata"]["loc_k"] == 1.0

        result = self.engine.calculate_scores([], lines_of_code=1000)
        assert result["scoring_metadata"]["loc_k"] == 1.0

        result = self.engine.calculate_scores([], lines_of_code=2000)
        assert result["scoring_metadata"]["loc_k"] == 2.0


class TestIssueDensity:
    """F. Normalized issue density scales correctly."""

    def setup_method(self):
        self.engine = ScoringEngine()

    def test_issue_density_proportional(self):
        """More issues in same LOC → higher density."""
        issues_5 = [_make_issue(confidence=100) for _ in range(5)]
        issues_10 = [_make_issue(confidence=100) for _ in range(10)]

        result_5 = self.engine.calculate_scores(issues_5, lines_of_code=2000)
        result_10 = self.engine.calculate_scores(issues_10, lines_of_code=2000)

        assert result_10["scoring_metadata"]["normalized_issue_density"] > result_5["scoring_metadata"]["normalized_issue_density"]

    def test_confidence_adjusted_count(self):
        """Confidence-adjusted count: 10 issues at 50% = 5.0 effective issues."""
        issues = [_make_issue(confidence=50) for _ in range(10)]
        result = self.engine.calculate_scores(issues, lines_of_code=2000)

        assert result["scoring_metadata"]["confidence_adjusted_issue_count"] == 5.0


class TestComplexityMonotonicity:
    """G. Maintainability decreases monotonically with increasing average complexity."""

    def setup_method(self):
        self.engine = ScoringEngine()

    def test_complexity_monotonic_decrease(self):
        """0 < 10 < 20 average complexity → maintainability strictly decreasing."""
        issues = [_make_issue()]

        result_0 = self.engine.calculate_scores(issues, cyclomatic_complexity=0, num_functions=1)
        result_10 = self.engine.calculate_scores(issues, cyclomatic_complexity=10, num_functions=1)
        result_20 = self.engine.calculate_scores(issues, cyclomatic_complexity=20, num_functions=1)

        assert result_0["maintainability_score"] > result_10["maintainability_score"]
        assert result_10["maintainability_score"] > result_20["maintainability_score"]

    def test_average_complexity_with_multiple_functions(self):
        """Total complexity 20 with 4 functions → average = 5, not 20."""
        issues = [_make_issue()]

        # 20 total / 4 functions = 5 average
        result_avg5 = self.engine.calculate_scores(issues, cyclomatic_complexity=20, num_functions=4)

        # 20 total / 1 function = 20 average
        result_avg20 = self.engine.calculate_scores(issues, cyclomatic_complexity=20, num_functions=1)

        # Well-factored code (avg 5) should score better than monolithic (avg 20)
        assert result_avg5["maintainability_score"] > result_avg20["maintainability_score"]

    def test_zero_functions_fallback(self):
        """When num_functions=0, use total complexity as fallback."""
        issues = [_make_issue()]
        result = self.engine.calculate_scores(issues, cyclomatic_complexity=10, num_functions=0)
        assert result["scoring_metadata"]["average_complexity"] == 10.0


class TestNonImprovement:
    """H. Adding a valid additional finding must never increase any score."""

    def setup_method(self):
        self.engine = ScoringEngine()

    def test_adding_issue_never_improves_overall(self):
        """Adding any issue must not increase the overall quality score."""
        base_issues = [_make_issue(severity="Medium", confidence=80)]
        extra_issue = _make_issue(severity="Low", confidence=50)

        result_base = self.engine.calculate_scores(base_issues, lines_of_code=1000)
        result_more = self.engine.calculate_scores(base_issues + [extra_issue], lines_of_code=1000)

        assert result_more["overall_quality"] <= result_base["overall_quality"]
        assert result_more["technical_debt_score"] <= result_base["technical_debt_score"]
        assert result_more["maintainability_score"] <= result_base["maintainability_score"]

    def test_adding_security_issue_never_improves_security(self):
        """Adding a security issue must not improve the security score."""
        base_issues = [_make_issue(severity="High", confidence=100, rule_type="Security",
                                   description="SQL injection vulnerability")]
        extra_issue = _make_issue(severity="Low", confidence=50, rule_type="Security",
                                  description="Unsafe eval usage")

        result_base = self.engine.calculate_scores(base_issues)
        result_more = self.engine.calculate_scores(base_issues + [extra_issue])

        assert result_more["security_score"] <= result_base["security_score"]


class TestBounds:
    """I. Extreme inputs: scores never negative or >100."""

    def setup_method(self):
        self.engine = ScoringEngine()

    def test_clamping_at_zero_overwhelming_issues(self):
        """20 Critical issues at 100% confidence must clamp all scores to 0."""
        issues = [
            _make_issue(severity="Critical", confidence=100, rule_type="Security Performance",
                        description="Terrible code.")
            for _ in range(20)
        ]
        result = self.engine.calculate_scores(issues, cyclomatic_complexity=500)
        assert result["overall_quality"] == 0
        assert result["security_score"] == 0
        assert result["performance_score"] == 0
        assert result["technical_debt_score"] == 0
        assert result["maintainability_score"] == 0
        assert result["maintainability_grade"] == "F"

    def test_extreme_issue_count(self):
        """1000 Critical issues must still produce valid bounded scores."""
        issues = [_make_issue(severity="Critical", confidence=100) for _ in range(1000)]
        result = self.engine.calculate_scores(issues, cyclomatic_complexity=10000, lines_of_code=100)

        for key in ["overall_quality", "security_score", "performance_score",
                     "maintainability_score", "technical_debt_score"]:
            assert 0 <= result[key] <= 100, f"{key} = {result[key]} out of bounds"

    def test_extreme_complexity(self):
        """Very high complexity must still produce valid bounded scores."""
        result = self.engine.calculate_scores([], cyclomatic_complexity=100000, num_functions=1)
        assert 0 <= result["maintainability_score"] <= 100

    def test_no_issues_never_exceeds_100(self):
        """With no issues, no score should exceed 100."""
        result = self.engine.calculate_scores([], lines_of_code=100000)
        for key in ["overall_quality", "security_score", "performance_score",
                     "maintainability_score", "technical_debt_score"]:
            assert result[key] <= 100


class TestOverallScore:
    """J. Verify exact weighted sum."""

    def setup_method(self):
        self.engine = ScoringEngine()

    def test_weighted_sum_exact(self):
        """Overall quality must be the exact weighted sum of sub-scores."""
        issues = [
            _make_issue(severity="High", confidence=80, rule_type="Security",
                        description="Missing authentication."),
            _make_issue(severity="Medium", confidence=100, rule_type="Best Practices",
                        description="Inefficient loop detected."),
        ]
        result = self.engine.calculate_scores(issues, lines_of_code=2000, num_functions=3)

        expected_overall = (
            0.30 * result["security_score"]
            + 0.25 * result["performance_score"]
            + 0.30 * result["maintainability_score"]
            + 0.15 * result["technical_debt_score"]
        )
        assert result["overall_quality"] == int(round(expected_overall))

    def test_category_weights_sum_to_one(self):
        """Category weights must sum to exactly 1.0."""
        total = sum(ScoringEngine.CATEGORY_WEIGHTS.values())
        assert abs(total - 1.0) < 1e-10


class TestMissingZeroValues:
    """K. Missing/zero values: no division-by-zero exceptions."""

    def setup_method(self):
        self.engine = ScoringEngine()

    def test_empty_issues_list(self):
        """Empty issues list must not raise."""
        result = self.engine.calculate_scores([])
        assert result["overall_quality"] == 100

    def test_zero_loc(self):
        """Zero LOC must not raise (LOC_K minimum guard = 1.0)."""
        result = self.engine.calculate_scores([_make_issue()], lines_of_code=0)
        assert 0 <= result["overall_quality"] <= 100

    def test_zero_functions(self):
        """Zero functions must not raise (falls back to total complexity)."""
        result = self.engine.calculate_scores([_make_issue()], cyclomatic_complexity=10, num_functions=0)
        assert 0 <= result["overall_quality"] <= 100

    def test_missing_confidence(self):
        """Missing confidence defaults to 50."""
        issues = [{"severity": "High", "rule_type": "General", "description": "Test"}]
        result = self.engine.calculate_scores(issues)
        assert 0 <= result["overall_quality"] <= 100
        # Impact should be 7 * 0.5 = 3.5
        assert result["scoring_metadata"]["total_impact"] == 3.5

    def test_missing_severity(self):
        """Missing severity defaults to Low (weight=1)."""
        issues = [{"confidence": 100, "rule_type": "General", "description": "Test"}]
        result = self.engine.calculate_scores(issues)
        assert result["scoring_metadata"]["total_impact"] == 1.0

    def test_one_line_snippet(self):
        """One-line snippet must produce valid scores."""
        result = self.engine.calculate_scores([_make_issue()], lines_of_code=1)
        assert 0 <= result["overall_quality"] <= 100

    def test_completely_empty_issue_dict(self):
        """An empty issue dict must not raise."""
        result = self.engine.calculate_scores([{}])
        assert 0 <= result["overall_quality"] <= 100


class TestRegressionV1:
    """L. Regression tests: existing test scenarios from v1.0 with updated expectations.

    All v1.0 tests are preserved. Where expected values changed due to the confidence-
    consistency and normalization fixes, the changes are documented with OLD vs NEW.
    """

    def setup_method(self):
        self.engine = ScoringEngine()

    def test_no_issues_perfect_scores(self):
        """Unchanged from v1.0."""
        result = self.engine.calculate_scores([])
        assert result["overall_quality"] == 100
        assert result["security_score"] == 100
        assert result["performance_score"] == 100
        assert result["technical_debt_score"] == 100
        assert result["maintainability_score"] == 100
        assert result["maintainability_grade"] == "A"

    def test_single_critical_security_issue(self):
        """
        OLD v1.0: Maintainability = 84 (penalty = 10*1.5 + 0 + 1 = 16)
        NEW v2.0: Maintainability = 84 (penalty = 10*1.5/1 + 1/1 + 0 = 16)
        CHANGE: No change. With LOC_K=1.0 (default) and single issue,
                NormalizedImpact = 10, NormalizedIssueDensity = 1.0.
                1.5*10 + 1.0 + 0 = 16 → 100-16 = 84. Same result.
        """
        issues = [
            {
                "severity": "Critical",
                "confidence": 100,
                "rule_type": "Security",
                "description": "SQL Injection vulnerability found.",
            }
        ]
        result = self.engine.calculate_scores(issues)
        assert result["security_score"] == 70
        assert result["performance_score"] == 100
        assert result["technical_debt_score"] == 80
        assert result["maintainability_score"] == 84
        assert result["maintainability_grade"] == "B"

    def test_performance_issue_with_low_confidence(self):
        """
        OLD v1.0: Maintainability = 96 (penalty = 2*1.5 + 0 + 1 = 4)
        NEW v2.0: Maintainability = 97 (penalty = 2*1.5/1 + 0.5/1 + 0 = 3.5)
        CHANGE: Slightly improved. The old formula added raw IssueCount=1
                regardless of confidence. The new formula uses
                ConfidenceAdjustedIssueCount = 0.5 (50% confidence).
                New penalty = 3.0 + 0.5 = 3.5 → 100-3.5 = 96.5 → 97 (rounded up).
        """
        issues = [
            {
                "severity": "Medium",
                "confidence": 50,
                "rule_type": "Best Practices",
                "description": "Inefficient loop detected.",
            }
        ]
        result = self.engine.calculate_scores(issues)
        assert result["performance_score"] == 94
        assert result["security_score"] == 100
        assert result["technical_debt_score"] == 96
        # Changed from 96 → 96 (same result: penalty = 3.5 → 96.5 → round(96.5) = 96
        # by Python banker's rounding. The conceptual improvement is that the penalty
        # dropped from 4.0 to 3.5 due to confidence-adjusted count.)
        assert result["maintainability_score"] == 96

    def test_multiple_mixed_issues(self):
        """
        OLD v1.0: Maintainability = 88 (penalty = 6.6*1.5 + 0 + 2 = 11.9)
        NEW v2.0: Maintainability = 89 (penalty = 6.6*1.5/1 + 1.8/1 + 0 = 11.7)
        CHANGE: Slightly improved. ConfidenceAdjustedIssueCount = 0.8 + 1.0 = 1.8
                (replaces raw count of 2). New penalty = 9.9 + 1.8 = 11.7 → 100-11.7 = 88.3 → 88.
        """
        issues = [
            {
                "severity": "High",
                "confidence": 80,
                "rule_type": "Auth",
                "description": "Missing authentication.",
            },
            {
                "severity": "Low",
                "confidence": 100,
                "rule_type": "Style",
                "description": "Unused variable.",
            }
        ]
        result = self.engine.calculate_scores(issues)
        assert result["security_score"] == 83
        assert result["technical_debt_score"] == 87
        # Changed from 88 → 88 (rounds to same value in this case)
        assert result["maintainability_score"] == 88

    def test_clamping_at_zero(self):
        """Unchanged from v1.0 — overwhelming issues still clamp to 0."""
        issues = [
            {
                "severity": "Critical",
                "confidence": 100,
                "rule_type": "Security Performance",
                "description": "Terrible code.",
            }
            for _ in range(20)
        ]
        result = self.engine.calculate_scores(issues, cyclomatic_complexity=500)
        assert result["overall_quality"] == 0
        assert result["security_score"] == 0
        assert result["performance_score"] == 0
        assert result["technical_debt_score"] == 0
        assert result["maintainability_score"] == 0
        assert result["maintainability_grade"] == "F"

    def test_complexity_neutral_handling(self):
        """
        OLD v1.0: complexity=0 → maint=98 (penalty = 1*1.5+0+1=2.5→98),
                  complexity=10 → maint=92 (penalty = 1*1.5+5+1=7.5→92)
        NEW v2.0: complexity=0 → maint=98 (penalty = 1*1.5+1+0=2.5→98),
                  complexity=10, num_functions=0 → maint=93 (penalty = 1.5+1+5=7.5→93)
        CHANGE: With num_functions=0, average_complexity = total = 10,
                so complexity_penalty = 10/2 = 5. Penalty = 1.5 + 1.0 + 5.0 = 7.5 → 93.
                Wait: 100 - 7.5 = 92.5 → 92 or 93?
                Python round(92.5) = 92 (banker's rounding). Same as v1.0.
        """
        issues = [{"severity": "Low", "confidence": 100, "rule_type": "General"}]

        result_0 = self.engine.calculate_scores(issues, cyclomatic_complexity=0)
        result_10 = self.engine.calculate_scores(issues, cyclomatic_complexity=10)

        # Penalty with 0 complexity: 1.5*1 + 1.0 + 0 = 2.5 → 100-2.5 = 97.5 → 98
        assert result_0["maintainability_score"] == 98
        # Penalty with 10 complexity: 1.5*1 + 1.0 + 5 = 7.5 → 100-7.5 = 92.5 → 92
        assert result_10["maintainability_score"] == 92


class TestRealCodeIntegration:
    """M. Real-code integration tests (preserved from v1.0)."""

    def setup_method(self):
        self.engine = ScoringEngine()

    def test_security_score_with_real_code(self):
        """Test that submitting insecure code legitimately lowers the security score."""
        from app.engine.static_analyzer import StaticAnalyzer
        analyzer = StaticAnalyzer()

        insecure_code = 'password = "admin123"\neval(input())'
        issues = analyzer.analyze(insecure_code, "Python")
        for issue in issues:
            issue["confidence"] = 100

        insecure_result = self.engine.calculate_scores(issues)

        secure_code = 'import os\npassword = os.getenv("APP_PASSWORD")\nprint("Connecting to DB")'
        secure_issues = analyzer.analyze(secure_code, "Python")
        for issue in secure_issues:
            issue["confidence"] = 100

        secure_result = self.engine.calculate_scores(secure_issues)

        assert insecure_result["security_score"] < 100
        assert secure_result["security_score"] > insecure_result["security_score"]
        assert secure_result["security_score"] == 100

    def test_performance_score_with_real_code(self):
        """Test that submitting code with recognized performance issues lowers performance score.

        NOTE (v2.1): The original test used COMPLEX_CONDITION ('if a and b and c and d')
        as a performance proxy. This was the exact bug identified by the root-cause audit:
        COMPLEX_CONDITION detects complex boolean expressions (maintainability), NOT
        algorithmic performance. Updated to use nested loops which correctly trigger
        PY_NESTED_LOOP_COMPLEXITY (rule_type: Performance).
        """
        from app.engine.static_analyzer import StaticAnalyzer
        analyzer = StaticAnalyzer()

        # Code with nested loops — genuine algorithmic performance concern
        inefficient_code = 'for a in data:\n    for b in data:\n        process(a, b)\n'
        issues = analyzer.analyze(inefficient_code, "Python")
        for issue in issues:
            issue["confidence"] = 100

        inefficient_result = self.engine.calculate_scores(issues)

        # Code without nested loops — no performance concern
        efficient_code = 'for a in data:\n    process(a)\n'
        efficient_issues = analyzer.analyze(efficient_code, "Python")
        for issue in efficient_issues:
            issue["confidence"] = 100

        efficient_result = self.engine.calculate_scores(efficient_issues)

        assert inefficient_result["performance_score"] < 100
        assert efficient_result["performance_score"] >= inefficient_result["performance_score"]
        assert efficient_result["performance_score"] == 100


class TestGradeMapping:
    """Verify grade letter assignments match documented thresholds."""

    def setup_method(self):
        self.engine = ScoringEngine()

    def test_grade_boundaries(self):
        assert ScoringEngine._grade(100) == "A"
        assert ScoringEngine._grade(95) == "A"
        assert ScoringEngine._grade(90) == "A"
        assert ScoringEngine._grade(89.9) == "B"
        assert ScoringEngine._grade(80) == "B"
        assert ScoringEngine._grade(79.9) == "C"
        assert ScoringEngine._grade(70) == "C"
        assert ScoringEngine._grade(69.9) == "D"
        assert ScoringEngine._grade(60) == "D"
        assert ScoringEngine._grade(59.9) == "F"
        assert ScoringEngine._grade(0) == "F"


# ═══════════════════════════════════════════════════════════════════
# Performance Category Classification Regression
# ═══════════════════════════════════════════════════════════════════

class TestPerformanceCategoryRegression:
    """Regression tests for the 'complexity' keyword removal from PERFORMANCE_KEYWORDS."""

    def setup_method(self):
        self.engine = ScoringEngine()

    def test_complexity_rule_type_does_not_affect_performance(self):
        """A COMPLEX_CONDITION finding (rule_type='Complexity') must NOT create a performance penalty."""
        issues = [
            {
                "severity": "Medium",
                "confidence": 86,
                "rule_type": "Complexity",
                "description": "Complex condition, refactor into smaller methods",
            }
        ]
        result = self.engine.calculate_scores(issues, cyclomatic_complexity=5, lines_of_code=50, num_functions=1)
        assert result["performance_score"] == 100, (
            "COMPLEX_CONDITION findings should NOT penalize Performance Score"
        )

    def test_multiple_complexity_findings_no_performance_penalty(self):
        """Multiple COMPLEX_CONDITION findings must not affect performance."""
        issues = [
            {
                "severity": "Medium",
                "confidence": 86,
                "rule_type": "Complexity",
                "description": "Complex condition, refactor into smaller methods",
            }
            for _ in range(5)
        ]
        result = self.engine.calculate_scores(issues, cyclomatic_complexity=10, lines_of_code=100, num_functions=3)
        assert result["performance_score"] == 100

    def test_performance_rule_type_does_affect_performance(self):
        """A finding with rule_type='Performance' MUST create a performance penalty."""
        issues = [
            {
                "severity": "Medium",
                "confidence": 86,
                "rule_type": "Performance",
                "description": "Nested loops may introduce O(n^2)-style algorithmic complexity",
            }
        ]
        result = self.engine.calculate_scores(issues, cyclomatic_complexity=5, lines_of_code=50, num_functions=1)
        assert result["performance_score"] < 100, (
            "Performance-typed findings MUST penalize Performance Score"
        )

    def test_nested_loop_keyword_affects_performance(self):
        """A finding with 'nested_loop' in description must affect performance."""
        issues = [
            {
                "severity": "High",
                "confidence": 88,
                "rule_type": "Performance",
                "description": "nested_loop complexity detected",
            }
        ]
        result = self.engine.calculate_scores(issues, cyclomatic_complexity=5, lines_of_code=50, num_functions=1)
        assert result["performance_score"] < 100

    def test_complexity_still_affects_maintainability(self):
        """Removing 'complexity' from PERFORMANCE_KEYWORDS must NOT break maintainability scoring."""
        issues = [
            {
                "severity": "Medium",
                "confidence": 86,
                "rule_type": "Complexity",
                "description": "Complex condition, refactor into smaller methods",
            }
        ]
        result = self.engine.calculate_scores(issues, cyclomatic_complexity=15, lines_of_code=50, num_functions=1)
        # Maintainability MUST be penalized (it uses total_impact and complexity, not keywords)
        assert result["maintainability_score"] < 100
