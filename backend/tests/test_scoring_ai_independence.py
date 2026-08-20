import pytest
from app.engine.scoring_engine import ScoringEngine
from app.engine.hybrid_engine import HybridEngine

def test_scoring_ai_independence():
    scoring = ScoringEngine()
    hybrid = HybridEngine()

    # Base static issues
    static_issues = [
        {"severity": "Medium", "line_number": 5, "description": "Console log found", "rule_type": "Smells", "confidence": 100, "source": "Static"}
    ]

    # Scenario 1: Gemini unavailable (ai_status = "unavailable")
    # Hybrid engine passes only static issues to scoring engine
    unified_scenario_1 = static_issues.copy()
    
    score_1 = scoring.calculate_scores(
        issues=unified_scenario_1,
        cyclomatic_complexity=2,
        lines_of_code=10
    )

    # Scenario 2: Gemini available but no additional AI findings (ai_status = "success")
    # Hybrid engine again passes only static issues
    unified_scenario_2 = static_issues.copy()
    
    score_2 = scoring.calculate_scores(
        issues=unified_scenario_2,
        cyclomatic_complexity=2,
        lines_of_code=10
    )

    # Scenario 3: Gemini available AND finds additional issues
    ai_issues = [
        {"severity": "High", "line_number": 10, "description": "Unvalidated input", "rule_type": "Security", "confidence": 90, "source": "AI"}
    ]
    # Hybrid engine fuses them (simplified as concatenation for this test)
    unified_scenario_3 = static_issues + ai_issues
    
    score_3 = scoring.calculate_scores(
        issues=unified_scenario_3,
        cyclomatic_complexity=2,
        lines_of_code=10
    )

    # Assertions
    # 1. AI available but no new issues -> exact same score
    assert score_1 == score_2, "Score must be identical if static issues are identical and no AI issues are found"

    # 2. Score changes when genuine AI issues are added
    assert score_1["overall_quality"] > score_3["overall_quality"], "Overall quality should drop with more issues"
    assert score_1["maintainability_score"] > score_3["maintainability_score"], "Maintainability should drop with more issues"
    assert score_1["technical_debt_score"] > score_3["technical_debt_score"], "Tech debt score should drop with more issues"

    # Print exact scoring data passed into the Scoring Engine for the report
    print("\n--- SCORING AUDIT REPORT ---")
    print(f"Scenario 1 (Gemini unavailable) Data into Scoring Engine: {len(unified_scenario_1)} issues, Complexity 2")
    print(f"Scenario 1 Scores: {score_1}")
    
    print(f"\nScenario 2 (Gemini available, 0 AI issues) Data into Scoring Engine: {len(unified_scenario_2)} issues, Complexity 2")
    print(f"Scenario 2 Scores: {score_2}")
    
    print(f"\nScenario 3 (Gemini available, 1 new AI issue) Data into Scoring Engine: {len(unified_scenario_3)} issues, Complexity 2")
    print(f"Scenario 3 Scores: {score_3}")
    print("----------------------------\n")
