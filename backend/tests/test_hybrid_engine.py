"""Tests for the Hybrid Review Engine.

Covers:
* Issue normalization (source tagging, severity coercion, defaults)
* Issue ID generation (sequential, deterministic within an engine instance)
* Weighted duplicate detection (line 40%, rule 30%, description 30%)
* Fusion logic (Static-only, AI-only, merged duplicates, sorting, empties)
"""

from __future__ import annotations

import pytest

from app.engine.hybrid_engine import HybridEngine, NormalizedIssue, _text_similarity


# ──────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────


@pytest.fixture
def engine() -> HybridEngine:
    """Return a fresh HybridEngine for each test."""
    return HybridEngine()


@pytest.fixture
def sample_static_issues() -> list[dict]:
    return [
        {
            "severity": "High",
            "line_number": 10,
            "description": "Catch-all exception handling masks bugs",
            "rule_type": "Bugs",
        },
        {
            "severity": "Low",
            "line_number": 25,
            "description": "TODO comments indicate incomplete code",
            "rule_type": "Best Practices",
        },
        {
            "severity": "critical",
            "line_number": 5,
            "description": "Possible hardcoded secret",
            "rule_type": "Security",
        },
    ]


@pytest.fixture
def sample_ai_issues() -> list[dict]:
    return [
        {
            "severity": "High",
            "line_number": 10,
            "description": "Catch-all exception handling masks bugs and hides errors",
            "rule_type": "Bugs",
            "ai_explanation": "Using a bare except catches all exceptions including KeyboardInterrupt.",
            "suggestion": "Use except Exception as e: instead",
        },
        {
            "severity": "Medium",
            "line_number": 42,
            "description": "Function is too complex, consider refactoring",
            "rule_type": "Complexity",
            "ai_explanation": "This function has a cyclomatic complexity of 15.",
        },
    ]


# ──────────────────────────────────────────────────────────────
# Text similarity helper
# ──────────────────────────────────────────────────────────────


class TestTextSimilarity:
    def test_identical_strings(self):
        assert _text_similarity("hello world", "hello world") == 1.0

    def test_completely_different(self):
        assert _text_similarity("alpha beta", "gamma delta") == 0.0

    def test_partial_overlap(self):
        sim = _text_similarity("catch all exception handling", "exception handling masks bugs")
        assert 0.0 < sim < 1.0

    def test_empty_strings(self):
        assert _text_similarity("", "") == 1.0

    def test_one_empty(self):
        assert _text_similarity("hello", "") == 0.0
        assert _text_similarity("", "hello") == 0.0

    def test_case_insensitive(self):
        assert _text_similarity("Hello World", "hello world") == 1.0


# ──────────────────────────────────────────────────────────────
# Normalization
# ──────────────────────────────────────────────────────────────


class TestNormalize:
    def test_tags_source_correctly(self, engine: HybridEngine):
        issues = [{"severity": "High", "line_number": 1, "description": "test", "rule_type": "Bugs"}]
        result = engine.normalize(issues, "Static")
        assert len(result) == 1
        assert result[0].source == "Static"

    def test_tags_ai_source(self, engine: HybridEngine):
        issues = [{"severity": "Low", "line_number": 5, "description": "x", "rule_type": "Smells"}]
        result = engine.normalize(issues, "AI")
        assert result[0].source == "AI"

    def test_coerces_severity_to_title_case(self, engine: HybridEngine):
        issues = [
            {"severity": "critical", "line_number": 1, "description": "a", "rule_type": "X"},
            {"severity": "HIGH", "line_number": 2, "description": "b", "rule_type": "Y"},
            {"severity": "medium", "line_number": 3, "description": "c", "rule_type": "Z"},
            {"severity": "LOW", "line_number": 4, "description": "d", "rule_type": "W"},
        ]
        result = engine.normalize(issues, "Static")
        assert [r.severity for r in result] == ["Critical", "High", "Medium", "Low"]

    def test_fills_missing_optional_fields(self, engine: HybridEngine):
        issues = [{"severity": "Low", "line_number": 1, "description": "test", "rule_type": "General"}]
        result = engine.normalize(issues, "Static")
        assert result[0].ai_explanation is None
        assert result[0].suggestion is None
        assert result[0].file is None

    def test_preserves_ai_explanation(self, engine: HybridEngine):
        issues = [
            {
                "severity": "High",
                "line_number": 10,
                "description": "test",
                "rule_type": "Bugs",
                "ai_explanation": "This is bad because...",
                "suggestion": "Do this instead",
            }
        ]
        result = engine.normalize(issues, "AI")
        assert result[0].ai_explanation == "This is bad because..."
        assert result[0].suggestion == "Do this instead"

    def test_preserves_file_field(self, engine: HybridEngine):
        issues = [
            {"severity": "Low", "line_number": 1, "description": "d", "rule_type": "X", "file": "src/main.py"}
        ]
        result = engine.normalize(issues, "Static")
        assert result[0].file == "src/main.py"

    def test_defaults_missing_severity_to_low(self, engine: HybridEngine):
        issues = [{"line_number": 1, "description": "x", "rule_type": "Y"}]
        result = engine.normalize(issues, "Static")
        assert result[0].severity == "Low"

    def test_defaults_missing_rule_type_to_general(self, engine: HybridEngine):
        issues = [{"severity": "Low", "line_number": 1, "description": "x"}]
        result = engine.normalize(issues, "Static")
        assert result[0].rule_type == "General"

    def test_empty_list(self, engine: HybridEngine):
        assert engine.normalize([], "Static") == []


# ──────────────────────────────────────────────────────────────
# Issue ID generation
# ──────────────────────────────────────────────────────────────


class TestIssueIdGeneration:
    def test_sequential_ids(self, engine: HybridEngine):
        issues = [
            {"severity": "Low", "line_number": i, "description": f"issue {i}", "rule_type": "X"}
            for i in range(1, 4)
        ]
        result = engine.normalize(issues, "Static")
        assert result[0].issue_id == "ISS-000001"
        assert result[1].issue_id == "ISS-000002"
        assert result[2].issue_id == "ISS-000003"

    def test_ids_unique_across_normalizations(self, engine: HybridEngine):
        static = engine.normalize(
            [{"severity": "Low", "line_number": 1, "description": "a", "rule_type": "X"}], "Static"
        )
        ai = engine.normalize(
            [{"severity": "Low", "line_number": 2, "description": "b", "rule_type": "Y"}], "AI"
        )
        assert static[0].issue_id != ai[0].issue_id

    def test_fresh_engine_resets_counter(self):
        e1 = HybridEngine()
        r1 = e1.normalize([{"severity": "Low", "line_number": 1, "description": "x", "rule_type": "X"}], "Static")
        e2 = HybridEngine()
        r2 = e2.normalize([{"severity": "Low", "line_number": 1, "description": "x", "rule_type": "X"}], "Static")
        assert r1[0].issue_id == r2[0].issue_id  # both ISS-000001

    def test_id_format(self, engine: HybridEngine):
        result = engine.normalize(
            [{"severity": "Low", "line_number": 1, "description": "x", "rule_type": "X"}], "Static"
        )
        assert result[0].issue_id.startswith("ISS-")
        assert len(result[0].issue_id) == 10  # "ISS-" + 6 digits


# ──────────────────────────────────────────────────────────────
# Weighted duplicate detection
# ──────────────────────────────────────────────────────────────


class TestDuplicateDetection:
    def _make_issue(self, engine, **kwargs) -> NormalizedIssue:
        defaults = {
            "severity": "High",
            "line_number": 10,
            "description": "Some issue description",
            "rule_type": "Bugs",
        }
        defaults.update(kwargs)
        return engine.normalize([defaults], "Static")[0]

    def test_exact_duplicate_scores_1(self, engine: HybridEngine):
        a = self._make_issue(engine, line_number=10, rule_type="Bugs", description="Catch-all exception")
        b = self._make_issue(engine, line_number=10, rule_type="Bugs", description="Catch-all exception")
        score = engine._duplicate_score(a, b)
        assert score == 1.0

    def test_same_line_same_rule_different_desc(self, engine: HybridEngine):
        a = self._make_issue(engine, line_number=10, rule_type="Bugs", description="alpha beta gamma")
        b = self._make_issue(engine, line_number=10, rule_type="Bugs", description="delta epsilon zeta")
        score = engine._duplicate_score(a, b)
        # line (40%) + rule (30%) + desc (0%) = 70%
        assert score == pytest.approx(0.70, abs=0.01)

    def test_same_line_different_rule_different_desc(self, engine: HybridEngine):
        a = self._make_issue(engine, line_number=10, rule_type="Bugs", description="alpha")
        b = self._make_issue(engine, line_number=10, rule_type="Security", description="beta")
        score = engine._duplicate_score(a, b)
        # line (40%) + rule (0%) + desc (0%) = 40%
        assert score == pytest.approx(0.40, abs=0.01)

    def test_different_line_same_rule_same_desc(self, engine: HybridEngine):
        a = self._make_issue(engine, line_number=10, rule_type="Bugs", description="same description")
        b = self._make_issue(engine, line_number=20, rule_type="Bugs", description="same description")
        score = engine._duplicate_score(a, b)
        # line (0%) + rule (30%) + desc (30%) = 60%
        assert score == pytest.approx(0.60, abs=0.01)

    def test_completely_different_scores_0(self, engine: HybridEngine):
        a = self._make_issue(engine, line_number=1, rule_type="Bugs", description="alpha")
        b = self._make_issue(engine, line_number=99, rule_type="Security", description="beta")
        score = engine._duplicate_score(a, b)
        assert score == pytest.approx(0.0, abs=0.01)

    def test_zero_line_numbers_dont_match(self, engine: HybridEngine):
        a = self._make_issue(engine, line_number=0, rule_type="Bugs", description="same")
        b = self._make_issue(engine, line_number=0, rule_type="Bugs", description="same")
        score = engine._duplicate_score(a, b)
        # line (0% — both zero) + rule (30%) + desc (30%) = 60%
        assert score == pytest.approx(0.60, abs=0.01)

    def test_partial_description_overlap(self, engine: HybridEngine):
        a = self._make_issue(
            engine, line_number=10, rule_type="Bugs",
            description="Catch-all exception handling masks bugs"
        )
        b = self._make_issue(
            engine, line_number=10, rule_type="Bugs",
            description="Catch-all exception handling masks bugs and hides errors"
        )
        score = engine._duplicate_score(a, b)
        # line (40%) + rule (30%) + desc (partial ~80%) → should be > 0.70
        assert score >= engine.DUPLICATE_THRESHOLD


# ──────────────────────────────────────────────────────────────
# Fusion
# ──────────────────────────────────────────────────────────────


class TestFuse:
    def test_static_only_preserved(self, engine: HybridEngine, sample_static_issues):
        static = engine.normalize(sample_static_issues, "Static")
        result = engine.fuse(static, [])
        assert len(result) == 3
        assert all(r["source"] == "Static" for r in result)

    def test_ai_only_preserved(self, engine: HybridEngine, sample_ai_issues):
        ai = engine.normalize(sample_ai_issues, "AI")
        result = engine.fuse([], ai)
        assert len(result) == 2
        assert all(r["source"] == "AI" for r in result)

    def test_duplicates_merged(self, engine: HybridEngine, sample_static_issues, sample_ai_issues):
        static = engine.normalize(sample_static_issues, "Static")
        ai = engine.normalize(sample_ai_issues, "AI")
        result = engine.fuse(static, ai)

        # The catch-all exception issue (line 10, Bugs) should be merged
        merged = [r for r in result if r["source"] == "Static + AI"]
        assert len(merged) == 1
        assert merged[0]["line_number"] == 10
        assert merged[0]["rule_type"] == "Bugs"
        assert merged[0]["ai_explanation"] is not None
        assert merged[0]["suggestion"] is not None
        assert "match_score" in merged[0]
        assert merged[0]["match_score"] >= engine.DUPLICATE_THRESHOLD

    def test_unmatched_static_kept(self, engine: HybridEngine, sample_static_issues, sample_ai_issues):
        static = engine.normalize(sample_static_issues, "Static")
        ai = engine.normalize(sample_ai_issues, "AI")
        result = engine.fuse(static, ai)

        static_only = [r for r in result if r["source"] == "Static"]
        # The TODO (line 25) and hardcoded secret (line 5) should remain Static
        assert len(static_only) == 2

    def test_unmatched_ai_kept(self, engine: HybridEngine, sample_static_issues, sample_ai_issues):
        static = engine.normalize(sample_static_issues, "Static")
        ai = engine.normalize(sample_ai_issues, "AI")
        result = engine.fuse(static, ai)

        ai_only = [r for r in result if r["source"] == "AI"]
        # The complexity issue (line 42) should remain AI
        assert len(ai_only) == 1
        assert ai_only[0]["line_number"] == 42

    def test_sorted_by_severity_then_line(self, engine: HybridEngine, sample_static_issues, sample_ai_issues):
        static = engine.normalize(sample_static_issues, "Static")
        ai = engine.normalize(sample_ai_issues, "AI")
        result = engine.fuse(static, ai)

        severities = [r["severity"] for r in result]
        severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        severity_keys = [severity_order[s] for s in severities]
        assert severity_keys == sorted(severity_keys)

    def test_empty_inputs(self, engine: HybridEngine):
        assert engine.fuse([], []) == []

    def test_all_issues_have_issue_id(self, engine: HybridEngine, sample_static_issues, sample_ai_issues):
        static = engine.normalize(sample_static_issues, "Static")
        ai = engine.normalize(sample_ai_issues, "AI")
        result = engine.fuse(static, ai)

        for issue in result:
            assert "issue_id" in issue
            assert issue["issue_id"].startswith("ISS-")

    def test_all_issues_have_source(self, engine: HybridEngine, sample_static_issues, sample_ai_issues):
        static = engine.normalize(sample_static_issues, "Static")
        ai = engine.normalize(sample_ai_issues, "AI")
        result = engine.fuse(static, ai)

        valid_sources = {"Static", "AI", "Static + AI"}
        for issue in result:
            assert issue["source"] in valid_sources

    def test_merged_uses_higher_severity(self, engine: HybridEngine):
        static = engine.normalize(
            [{"severity": "Medium", "line_number": 10, "description": "same issue here", "rule_type": "Bugs"}],
            "Static",
        )
        ai = engine.normalize(
            [{"severity": "Critical", "line_number": 10, "description": "same issue here", "rule_type": "Bugs"}],
            "AI",
        )
        result = engine.fuse(static, ai)
        merged = [r for r in result if r["source"] == "Static + AI"]
        assert len(merged) == 1
        assert merged[0]["severity"] == "Critical"

    def test_to_dict_excludes_none_values(self, engine: HybridEngine):
        issues = engine.normalize(
            [{"severity": "Low", "line_number": 1, "description": "test", "rule_type": "X"}], "Static"
        )
        result = engine.fuse(issues, [])
        # ai_explanation, suggestion, file, match_score should not appear in dicts
        for r in result:
            assert "ai_explanation" not in r
            assert "suggestion" not in r
            assert "file" not in r
            assert "match_score" not in r

    def test_no_double_counting(self, engine: HybridEngine):
        """A static issue should only match one AI issue, not multiple."""
        static = engine.normalize(
            [{"severity": "High", "line_number": 10, "description": "catch exception", "rule_type": "Bugs"}],
            "Static",
        )
        ai = engine.normalize(
            [
                {"severity": "High", "line_number": 10, "description": "catch exception handling", "rule_type": "Bugs"},
                {"severity": "High", "line_number": 10, "description": "catch exception masks bugs", "rule_type": "Bugs"},
            ],
            "AI",
        )
        result = engine.fuse(static, ai)
        merged = [r for r in result if r["source"] == "Static + AI"]
        ai_only = [r for r in result if r["source"] == "AI"]
        assert len(merged) == 1  # only one merge
        assert len(ai_only) == 1  # the other AI issue stays standalone

    def test_syntax_and_ai_bug_fusion(self, engine: HybridEngine):
        """A syntax error from static analysis and a bug from AI on the same line should merge into a Syntax issue."""
        static = engine.normalize(
            [{"severity": "Critical", "line_number": 6, "description": "Java syntax error: malformed string literal", "rule_type": "Syntax"}],
            "Static",
        )
        ai = engine.normalize(
            [{"severity": "Critical", "line_number": 6, "description": "String literal is missing closing quote", "rule_type": "Bugs", "ai_explanation": "You forgot a quote."}],
            "AI",
        )
        result = engine.fuse(static, ai)
        assert len(result) == 1
        merged = result[0]
        assert merged["source"] == "Static + AI"
        assert merged["rule_type"] == "Syntax"
        assert merged["ai_explanation"] == "You forgot a quote."
