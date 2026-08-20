"""CodePilot Confidence Engine.

Calculates a deterministic confidence score for every normalized review issue.
The confidence score is between 0 and 100 and is based on:
1. Issue Source
2. Severity
3. Match Score (for merged issues)

This logic is independent of the Gemini AI provider.
"""

from typing import Any, Dict, List


class ConfidenceEngine:
    def __init__(self) -> None:
        pass

    def calculate(self, issue: Dict[str, Any]) -> int:
        """Calculate the confidence score (0-100) for a single issue dict."""
        source = issue.get("source", "")
        severity = issue.get("severity", "Low")
        match_score = issue.get("match_score")

        # 1. Base Score from Source
        if source == "Static + AI":
            score = 95
        elif source == "Static":
            score = 85
        elif source == "AI":
            score = 70
        else:
            score = 50  # Fallback for unknown sources

        # 2. Severity Adjustment
        severity_adj = {
            "Critical": 5,
            "High": 3,
            "Medium": 1,
            "Low": 0,
        }
        # handle case-insensitive or missing keys gracefully
        adj = 0
        for k, v in severity_adj.items():
            if severity.lower() == k.lower():
                adj = v
                break
        score += adj

        # 3. Match Strength Adjustment
        if match_score is not None:
            if match_score >= 0.9:
                score += 5
            elif match_score >= 0.7:
                score += 3

        # 4. Clamp
        return max(0, min(100, score))

    def calculate_all(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate confidence for all issues and inject the 'confidence' key."""
        for issue in issues:
            issue["confidence"] = self.calculate(issue)
        return issues
