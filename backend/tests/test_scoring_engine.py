"""Tests for the CodePilot Scoring Engine.

Covers:
* Deterministic scoring based on unified issues.
* Security, Performance, Tech Debt, Maintainability scores.
* Neutral handling of defaults.
* Clamping at 0 and 100.
"""

from app.engine.scoring_engine import ScoringEngine


class TestScoringEngine:
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

    def test_single_critical_security_issue(self):
        issues = [
            {
                "severity": "Critical",
                "confidence": 100,
                "rule_type": "Security",
                "description": "SQL Injection vulnerability found.",
            }
        ]
        result = self.engine.calculate_scores(issues)
        # Impact = 10 (Critical) * 1.0 (confidence) = 10
        # Security Penalty = 10 * 3 = 30 -> Score 70
        assert result["security_score"] == 70
        # Performance Penalty = 0 -> Score 100
        assert result["performance_score"] == 100
        # Tech Debt Penalty = 10 * 2 = 20 -> Score 80
        assert result["technical_debt_score"] == 80
        # Maintainability Penalty = (10 * 1.5) + 0 + 1 = 16 -> Score 84
        assert result["maintainability_score"] == 84
        assert result["maintainability_grade"] == "B"

    def test_performance_issue_with_low_confidence(self):
        issues = [
            {
                "severity": "Medium", # Weight 4
                "confidence": 50,     # Factor 0.5 -> Impact 2
                "rule_type": "Best Practices",
                "description": "Inefficient loop detected.",
            }
        ]
        result = self.engine.calculate_scores(issues)
        # Performance Penalty = 2 * 3 = 6 -> Score 94
        assert result["performance_score"] == 94
        assert result["security_score"] == 100
        # Tech Debt Penalty = 2 * 2 = 4 -> Score 96
        assert result["technical_debt_score"] == 96
        # Maintainability Penalty = (2 * 1.5) + 0 + 1 = 4 -> Score 96
        assert result["maintainability_score"] == 96

    def test_multiple_mixed_issues(self):
        issues = [
            {
                "severity": "High", # 7
                "confidence": 80,   # 0.8 -> Impact 5.6
                "rule_type": "Auth",
                "description": "Missing authentication.", # Security
            },
            {
                "severity": "Low",  # 1
                "confidence": 100,  # 1.0 -> Impact 1
                "rule_type": "Style",
                "description": "Unused variable.",
            }
        ]
        result = self.engine.calculate_scores(issues)
        # Total impact = 6.6
        # Security Penalty = 5.6 * 3 = 16.8 -> Score 83
        assert result["security_score"] == 83
        # Tech Debt Penalty = 6.6 * 2 = 13.2 -> Score 87
        assert result["technical_debt_score"] == 87
        # Maintainability Penalty = (6.6 * 1.5) + 0 + 2 = 11.9 -> Score 88 (B)
        assert result["maintainability_score"] == 88

    def test_clamping_at_zero(self):
        # Create overwhelming issues to force scores < 0
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
        issues = [{"severity": "Low", "confidence": 100, "rule_type": "General"}]
        
        # When complexity is 0, penalty from complexity is 0
        result_0 = self.engine.calculate_scores(issues, cyclomatic_complexity=0)
        
        # When complexity is > 0, penalty is applied
        result_10 = self.engine.calculate_scores(issues, cyclomatic_complexity=10)
        
        # Maintainability penalty diff is roughly 5 (10 / 2) but rounding to even can shift it
        assert result_0["maintainability_score"] == 98
        assert result_10["maintainability_score"] == 92

    def test_security_score_with_real_code(self):
        """Test that submitting insecure code legitimately lowers the security score."""
        from app.engine.static_analyzer import StaticAnalyzer
        analyzer = StaticAnalyzer()
        
        # 1. Insecure code
        insecure_code = 'password = "admin123"\neval(input())'
        issues = analyzer.analyze(insecure_code, "Python")
        # Hardcoded secret rule should catch the password assignment
        
        # We need to simulate the normalization that HybridEngine does,
        # but ScoringEngine just expects severity, confidence, rule_type, description.
        # Since static analyzer issues don't have confidence, we inject it like HybridEngine would
        for issue in issues:
            issue["confidence"] = 100
            
        insecure_result = self.engine.calculate_scores(issues)
        
        # 2. Secure code
        secure_code = 'import os\npassword = os.getenv("APP_PASSWORD")\nprint("Connecting to DB")'
        secure_issues = analyzer.analyze(secure_code, "Python")
        for issue in secure_issues:
            issue["confidence"] = 100
            
        secure_result = self.engine.calculate_scores(secure_issues)
        
        # Verify insecure < 100
        assert insecure_result["security_score"] < 100
        
        # Verify secure > insecure
        assert secure_result["security_score"] > insecure_result["security_score"]
        # Secure code might have a print statement smell, but no security issues
        assert secure_result["security_score"] == 100

    def test_performance_score_with_real_code(self):
        """Test that submitting code with recognized performance/complexity issues lowers performance score."""
        from app.engine.static_analyzer import StaticAnalyzer
        analyzer = StaticAnalyzer()
        
        # 1. Inefficient/complex code
        # The static analyzer recognizes complex conditions (Complexity) as a performance penalty
        inefficient_code = 'if a and b and c and d:\n    pass'
        issues = analyzer.analyze(inefficient_code, "Python")
        for issue in issues:
            issue["confidence"] = 100
            
        inefficient_result = self.engine.calculate_scores(issues)
        
        # 2. Efficient/simple code
        efficient_code = 'if a:\n    if b:\n        pass'
        efficient_issues = analyzer.analyze(efficient_code, "Python")
        for issue in efficient_issues:
            issue["confidence"] = 100
            
        efficient_result = self.engine.calculate_scores(efficient_issues)
        
        # Verify inefficient < 100
        assert inefficient_result["performance_score"] < 100
        
        # Verify efficient > inefficient
        assert efficient_result["performance_score"] > inefficient_result["performance_score"]
        assert efficient_result["performance_score"] == 100
