"""CodePilot Scoring Engine.

Calculates deterministic scores (Quality, Security, Performance, Maintainability, Tech Debt)
based on the normalized issues.
"""

from typing import Any, Dict, List


class ScoringEngine:
    def __init__(self) -> None:
        pass

    def calculate_scores(
        self,
        issues: List[Dict[str, Any]],
        cyclomatic_complexity: int = 0,
        lines_of_code: int = 0,
    ) -> Dict[str, Any]:
        """Calculate independent scores from the unified issues."""
        
        # 1. Normalize Severity Weights
        severity_weights = {
            "critical": 10,
            "high": 7,
            "medium": 4,
            "low": 1,
        }

        total_impact = 0.0
        security_penalty = 0.0
        performance_penalty = 0.0
        issue_count = len(issues)

        # Keywords for categorization
        security_keywords = {"security", "secret", "password", "credential", "injection", "authentication", "authorization", "eval", "unsafe"}
        performance_keywords = {"performance", "complexity", "inefficient", "loop", "algorithm", "resource"}

        for issue in issues:
            severity = str(issue.get("severity", "Low")).lower()
            weight = severity_weights.get(severity, 1)
            
            # Use confidence if available, otherwise assume 50 (neutral)
            confidence = float(issue.get("confidence", 50))
            confidence_factor = confidence / 100.0

            impact = weight * confidence_factor
            total_impact += impact

            # Check for categories in rule_type and description
            rule_type = str(issue.get("rule_type", "")).lower()
            description = str(issue.get("description", "")).lower()
            
            text_to_search = f"{rule_type} {description}"
            
            is_security = any(kw in text_to_search for kw in security_keywords)
            if is_security:
                security_penalty += impact
                
            is_performance = any(kw in text_to_search for kw in performance_keywords)
            if is_performance:
                performance_penalty += impact

        # 2. Security Score
        security_score = max(0.0, min(100.0, 100.0 - (security_penalty * 3)))

        # 3. Performance Score
        performance_score = max(0.0, min(100.0, 100.0 - (performance_penalty * 3)))

        # 4. Technical Debt Score (100 = Low Debt / Healthy, 0 = High Debt)
        technical_debt_score = max(0.0, min(100.0, 100.0 - (total_impact * 2)))

        # 5. Maintainability Score
        # If complexity is > 0, include it in penalty. Otherwise neutral (0).
        complexity_penalty = cyclomatic_complexity / 2.0 if cyclomatic_complexity > 0 else 0
        
        maint_penalty = (total_impact * 1.5) + complexity_penalty + (issue_count * 1.0)
        maintainability_score = max(0.0, min(100.0, 100.0 - maint_penalty))

        if maintainability_score >= 90:
            maintainability_grade = "A"
        elif maintainability_score >= 80:
            maintainability_grade = "B"
        elif maintainability_score >= 70:
            maintainability_grade = "C"
        elif maintainability_score >= 60:
            maintainability_grade = "D"
        else:
            maintainability_grade = "F"

        # 6. Overall Quality Score
        overall_quality = (
            (security_score * 0.30)
            + (performance_score * 0.25)
            + (maintainability_score * 0.30)
            + (technical_debt_score * 0.15)
        )
        overall_quality = max(0.0, min(100.0, overall_quality))

        return {
            "version": "1.0",
            "overall_quality": int(round(overall_quality)),
            "security_score": int(round(security_score)),
            "performance_score": int(round(performance_score)),
            "maintainability_score": int(round(maintainability_score)),
            "maintainability_grade": maintainability_grade,
            "technical_debt_score": int(round(technical_debt_score)),
        }
