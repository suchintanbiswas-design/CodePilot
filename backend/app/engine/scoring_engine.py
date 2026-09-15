"""CodePilot Scoring Engine v2.0

Calculates deterministic, size-normalized scores (Quality, Security, Performance,
Maintainability, Tech Debt Health) based on normalized issues.

=== Theoretical Foundations ===
- Software quality characteristics (Security, Performance, Maintainability)
  are informed by ISO/IEC 25010 quality model categories.
- EffectiveImpact = SeverityWeight × (Confidence / 100) has structural similarity
  to risk = likelihood × impact frameworks.
- Overall weighted aggregation follows a Weighted Sum Model (MCDA approach).

=== CodePilot-Specific Design ===
- All formulas, coefficients, and weights are CodePilot-specific calibration
  parameters. They are NOT direct ISO/IEC formulas, CVSS scores, or SQALE ratios.
- Initial calibration weights — subject to empirical validation.
- No empirical validation results have been fabricated.

=== Cyclomatic Complexity vs Algorithmic Complexity ===
These are fundamentally different metrics:
- Cyclomatic complexity (McCabe) counts the number of linearly independent paths
  through a program's source code. It measures control-flow decision complexity
  and is used in the Maintainability penalty formula.
- Algorithmic complexity (Big-O) describes how runtime or memory usage scales
  with input size. Nested loops can indicate polynomial runtime growth, but
  cyclomatic complexity alone cannot establish Big-O runtime.
Cyclomatic complexity is therefore NOT used in the Performance Score calculation.
Performance penalties are driven exclusively by findings explicitly categorized
as Performance issues by the analyzers.

=== v2.0 Changes (from v1.0) ===
- [BUG FIX] Maintainability no longer uses raw IssueCount (confidence-blind).
  Now uses ConfidenceAdjustedIssueCount for internal consistency.
- [NEW] Size normalization via LOC_K = max(LOC / 1000, 1.0).
- [NEW] NormalizedImpact and NormalizedIssueDensity replace absolute metrics.
- [NEW] AverageComplexity replaces total cyclomatic complexity to avoid
  penalizing well-factored code with many small functions.
- [NEW] Scoring metadata returned for transparency and validation.

=== v2.1 Changes (from v2.0) ===
- [BUG FIX] Removed "complexity" from PERFORMANCE_KEYWORDS. The COMPLEX_CONDITION
  rule (rule_type: "Complexity") detects complex boolean expressions, which is a
  maintainability concern, not an algorithmic performance issue. This was causing
  false performance penalties on clean code. Added "nested_loop" keyword instead.
"""

from typing import Any, Dict, List


class ScoringEngine:
    """CodePilot deterministic scoring engine.

    All coefficients are initial calibration parameters pending empirical validation.
    """

    # ─── Severity Weights ───────────────────────────────────────────────
    # Initial calibration weights — subject to empirical validation.
    # These are NOT CVSS base scores. They are CodePilot-specific ordinal weights
    # that encode the relative damage potential of each severity tier.
    SEVERITY_WEIGHTS = {
        "critical": 10,
        "high": 7,
        "medium": 4,
        "low": 1,
    }

    # ─── Category Weights ───────────────────────────────────────────────
    # Initial CodePilot calibration weights, pending empirical validation.
    # These are NOT ISO/IEC 25010 importance weights.
    # Sum = 1.0 (guarantees overall score ∈ [0, 100] when sub-scores ∈ [0, 100]).
    CATEGORY_WEIGHTS = {
        "security": 0.30,
        "performance": 0.25,
        "maintainability": 0.30,
        "technical_debt": 0.15,
    }

    # ─── Penalty Multipliers ───────────────────────────────────────────
    # CodePilot calibration parameters — not derived from established standards.
    SECURITY_PENALTY_MULTIPLIER = 3.0
    PERFORMANCE_PENALTY_MULTIPLIER = 3.0
    TECH_DEBT_PENALTY_MULTIPLIER = 2.0
    MAINT_IMPACT_MULTIPLIER = 1.5
    MAINT_COMPLEXITY_DIVISOR = 2.0

    # ─── Category Classification Keywords ──────────────────────────────
    SECURITY_KEYWORDS = frozenset({
        "security", "secret", "password", "credential", "injection",
        "authentication", "authorization", "eval", "unsafe",
    })
    # NOTE: "complexity" was intentionally removed from this set.
    # The COMPLEX_CONDITION rule (rule_type: "Complexity") detects complex boolean
    # expressions, which is a maintainability concern, NOT algorithmic performance.
    # Cyclomatic complexity ≠ algorithmic complexity.
    # Genuine performance findings should use explicit keywords like "performance",
    # "inefficient", "algorithm", or "nested_loop".
    PERFORMANCE_KEYWORDS = frozenset({
        "performance", "inefficient", "loop",
        "algorithm", "resource", "nested_loop",
    })

    def __init__(self) -> None:
        pass

    # ═══════════════════════════════════════════════════════════════════
    #  Public API
    # ═══════════════════════════════════════════════════════════════════

    def calculate_scores(
        self,
        issues: List[Dict[str, Any]],
        cyclomatic_complexity: int = 0,
        lines_of_code: int = 0,
        num_functions: int = 0,
    ) -> Dict[str, Any]:
        """Calculate independent, size-normalized scores from unified issues.

        Args:
            issues: List of normalized issue dicts (severity, confidence, rule_type, description).
            cyclomatic_complexity: Total cyclomatic complexity of the analyzed code.
            lines_of_code: Total lines of code (LOC) for size normalization.
            num_functions: Number of functions/methods detected. Used for average complexity.

        Returns:
            Dict with version, scores, grade, and scoring metadata for transparency.
        """
        # ── Step 1: Size normalization guard ──────────────────────────
        # LOC_K = max(LOC / 1000, 1.0)
        # Minimum guard prevents division by zero and prevents tiny snippets
        # from producing extreme normalized values.
        loc_k = max(lines_of_code / 1000.0, 1.0)

        # ── Step 2: Per-issue impact accumulation ────────────────────
        total_impact = 0.0
        security_impact = 0.0
        performance_impact = 0.0
        confidence_adjusted_issue_count = 0.0

        for issue in issues:
            severity = str(issue.get("severity", "Low")).lower()
            weight = self.SEVERITY_WEIGHTS.get(severity, 1)

            # Use confidence if available, otherwise assume 50 (neutral)
            confidence = float(issue.get("confidence", 50))
            confidence_factor = confidence / 100.0

            # EffectiveImpact_i = SeverityWeight_i × (Confidence_i / 100)
            impact = weight * confidence_factor
            total_impact += impact

            # Confidence-adjusted issue count: Σ(Confidence_i / 100)
            # This replaces the old raw IssueCount which was confidence-blind.
            confidence_adjusted_issue_count += confidence_factor

            # Categorize by keywords in rule_type and description
            rule_type = str(issue.get("rule_type", "")).lower()
            description = str(issue.get("description", "")).lower()
            text_to_search = f"{rule_type} {description}"

            if any(kw in text_to_search for kw in self.SECURITY_KEYWORDS):
                security_impact += impact

            if any(kw in text_to_search for kw in self.PERFORMANCE_KEYWORDS):
                performance_impact += impact

        # ── Step 3: Size-normalized metrics ──────────────────────────
        normalized_impact = total_impact / loc_k
        normalized_issue_density = confidence_adjusted_issue_count / loc_k

        # ── Step 4: Average complexity per function ──────────────────
        # Using average complexity prevents penalizing well-factored code
        # that has many small, simple functions.
        if num_functions > 0:
            average_complexity = cyclomatic_complexity / num_functions
        else:
            # If no function count available, use total complexity as fallback
            # (backwards compatible with callers that don't provide num_functions)
            average_complexity = float(cyclomatic_complexity)

        # ── Step 5: Security Score ───────────────────────────────────
        # SecurityPenalty = 3 × SecurityImpact
        # SecurityScore = clamp(100 - SecurityPenalty, 0, 100)
        security_penalty = self.SECURITY_PENALTY_MULTIPLIER * security_impact
        security_score = self._clamp(100.0 - security_penalty)

        # ── Step 6: Performance Score ────────────────────────────────
        # PerformancePenalty = 3 × PerformanceImpact
        # PerformanceScore = clamp(100 - PerformancePenalty, 0, 100)
        performance_penalty = self.PERFORMANCE_PENALTY_MULTIPLIER * performance_impact
        performance_score = self._clamp(100.0 - performance_penalty)

        # ── Step 7: Technical Debt Health ────────────────────────────
        # TechnicalDebtPenalty = 2 × NormalizedImpact
        # TechnicalDebtHealth = clamp(100 - TechnicalDebtPenalty, 0, 100)
        # Note: This is a CodePilot-specific health metric, NOT SQALE Technical Debt Ratio.
        tech_debt_penalty = self.TECH_DEBT_PENALTY_MULTIPLIER * normalized_impact
        technical_debt_score = self._clamp(100.0 - tech_debt_penalty)

        # ── Step 8: Maintainability Score ────────────────────────────
        # MaintainabilityPenalty =
        #     1.5 × NormalizedImpact
        #     + NormalizedIssueDensity
        #     + (AverageComplexity / 2)
        #
        # v2.0 FIX: Raw IssueCount replaced with NormalizedIssueDensity.
        # The old formula used raw IssueCount which was confidence-blind,
        # creating inconsistent treatment of uncertain findings.
        maint_penalty = (
            (self.MAINT_IMPACT_MULTIPLIER * normalized_impact)
            + normalized_issue_density
            + (average_complexity / self.MAINT_COMPLEXITY_DIVISOR)
        )
        maintainability_score = self._clamp(100.0 - maint_penalty)

        # Grade mapping
        maintainability_grade = self._grade(maintainability_score)

        # ── Step 9: Overall Quality Score ────────────────────────────
        # Weighted Sum Model: OverallQuality = Σ(w_i × Score_i)
        # Since Σ w_i = 1.0 and each Score_i ∈ [0,100], Overall ∈ [0,100].
        overall_quality = (
            (self.CATEGORY_WEIGHTS["security"] * security_score)
            + (self.CATEGORY_WEIGHTS["performance"] * performance_score)
            + (self.CATEGORY_WEIGHTS["maintainability"] * maintainability_score)
            + (self.CATEGORY_WEIGHTS["technical_debt"] * technical_debt_score)
        )
        overall_quality = self._clamp(overall_quality)

        return {
            "version": "2.0",
            "overall_quality": int(round(overall_quality)),
            "security_score": int(round(security_score)),
            "performance_score": int(round(performance_score)),
            "maintainability_score": int(round(maintainability_score)),
            "maintainability_grade": maintainability_grade,
            "technical_debt_score": int(round(technical_debt_score)),
            # ── Scoring Metadata (for transparency & validation) ─────
            "scoring_metadata": {
                "total_impact": round(total_impact, 4),
                "normalized_impact": round(normalized_impact, 4),
                "confidence_adjusted_issue_count": round(confidence_adjusted_issue_count, 4),
                "normalized_issue_density": round(normalized_issue_density, 4),
                "average_complexity": round(average_complexity, 4),
                "loc_k": round(loc_k, 4),
                "lines_of_code": lines_of_code,
                "num_functions": num_functions,
                "raw_issue_count": len(issues),
            },
        }

    # ═══════════════════════════════════════════════════════════════════
    #  Private helpers
    # ═══════════════════════════════════════════════════════════════════

    @staticmethod
    def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
        """Clamp value to [lo, hi]."""
        return max(lo, min(hi, value))

    @staticmethod
    def _grade(score: float) -> str:
        """Map a numeric score to a letter grade."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
