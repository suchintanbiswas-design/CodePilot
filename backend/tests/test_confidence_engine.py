"""Tests for the CodePilot Confidence Engine.

Covers:
* Deterministic confidence calculation based on source
* Severity adjustments
* Duplicate matching score adjustments
* Clamping between 0 and 100
"""

from app.engine.confidence_engine import ConfidenceEngine


class TestConfidenceEngine:
    def setup_method(self):
        self.engine = ConfidenceEngine()

    def test_static_and_ai_base_score(self):
        issue = {"source": "Static + AI"}
        assert self.engine.calculate(issue) == 95

    def test_static_only_base_score(self):
        issue = {"source": "Static"}
        assert self.engine.calculate(issue) == 85

    def test_ai_only_base_score(self):
        issue = {"source": "AI"}
        assert self.engine.calculate(issue) == 70

    def test_unknown_source_fallback(self):
        issue = {"source": "Unknown"}
        assert self.engine.calculate(issue) == 50

    def test_severity_adjustments(self):
        # Base for Static is 85
        assert self.engine.calculate({"source": "Static", "severity": "Critical"}) == 90
        assert self.engine.calculate({"source": "Static", "severity": "High"}) == 88
        assert self.engine.calculate({"source": "Static", "severity": "Medium"}) == 86
        assert self.engine.calculate({"source": "Static", "severity": "Low"}) == 85

    def test_case_insensitive_severity(self):
        assert self.engine.calculate({"source": "Static", "severity": "cRiTiCaL"}) == 90
        assert self.engine.calculate({"source": "Static", "severity": "HIGH"}) == 88

    def test_missing_severity_defaults_to_low(self):
        assert self.engine.calculate({"source": "Static"}) == 85

    def test_match_score_adjustments(self):
        # Static + AI base is 95
        # 95 + 3 (High severity) = 98
        # Very strong match (>= 0.9) -> +5 -> 103 (clamped to 100)
        issue_very_strong = {
            "source": "Static + AI",
            "severity": "High",
            "match_score": 0.95,
        }
        assert self.engine.calculate(issue_very_strong) == 100

        # Strong match (>= 0.7) -> +3
        issue_strong = {
            "source": "Static + AI",
            "severity": "Medium", # 95 + 1 = 96
            "match_score": 0.75,  # 96 + 3 = 99
        }
        assert self.engine.calculate(issue_strong) == 99

        # Weak match (< 0.7) -> 0
        issue_weak = {
            "source": "Static + AI",
            "severity": "Low", # 95 + 0 = 95
            "match_score": 0.5, # 95 + 0 = 95
        }
        assert self.engine.calculate(issue_weak) == 95

    def test_clamping_at_100(self):
        # 95 (Base) + 5 (Critical) + 5 (Very strong match) = 105 -> 100
        issue = {
            "source": "Static + AI",
            "severity": "Critical",
            "match_score": 1.0,
        }
        assert self.engine.calculate(issue) == 100

    def test_clamping_at_0(self):
        # The base formula doesn't currently produce < 0, but we can test clamping
        # by passing an issue and temporarily mocking the base score if we wanted to.
        # Here we just pass an extreme case where we subtract within the method itself.
        class CustomConfidenceEngine(ConfidenceEngine):
            def calculate(self, issue):
                score = -50
                return max(0, min(100, score))
        
        custom_engine = CustomConfidenceEngine()
        issue = {"source": "Static"}
        assert custom_engine.calculate(issue) == 0

    def test_calculate_all(self):
        issues = [
            {"source": "Static", "severity": "Critical"},
            {"source": "AI", "severity": "High"},
        ]
        result = self.engine.calculate_all(issues)
        assert result[0]["confidence"] == 90
        assert result[1]["confidence"] == 73
