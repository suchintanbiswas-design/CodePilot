"""Hybrid Review Engine — Normalizes and fuses static and AI analysis issues.

This module is the core novelty of CodePilot.  It takes heterogeneous issue
dicts produced by the StaticAnalyzer and the AIReviewer, normalises them into
a common shape, detects duplicates using a weighted-score algorithm, and
produces a single unified issue list.

Design notes
------------
* Pure logic — no database, no framework, no async.  Easy to unit-test.
* Each issue receives a deterministic ``issue_id`` (``ISS-NNNNNN``).
* Duplicate detection uses a three-axis weighted score:
      same line_number  → 40 %
      same rule_type    → 30 %
      description overlap → 30 %
  If the total score ≥ 0.70 the pair is treated as a duplicate.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Normalised issue model
# ---------------------------------------------------------------------------


@dataclass
class NormalizedIssue:
    """Common internal representation for every issue regardless of source."""

    issue_id: str
    severity: str
    line_number: int
    description: str
    rule_type: str
    source: str  # "Static", "AI", or "Static + AI"
    ai_explanation: Optional[str] = None
    suggestion: Optional[str] = None
    file: Optional[str] = None
    match_score: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a plain dict suitable for JSONB storage."""
        return {k: v for k, v in asdict(self).items() if v is not None}


# ---------------------------------------------------------------------------
# Severity ordering (for sorting)
# ---------------------------------------------------------------------------

_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _severity_key(severity: str) -> int:
    return _SEVERITY_ORDER.get(severity.lower(), 99)


# ---------------------------------------------------------------------------
# Text-similarity helper
# ---------------------------------------------------------------------------

_WORD_RE = re.compile(r"[a-zA-Z0-9]+")


def _tokenize(text: str) -> set[str]:
    """Return the set of lower-cased alphanumeric tokens in *text*."""
    return set(_WORD_RE.findall(text.lower()))


def _text_similarity(a: str, b: str) -> float:
    """Return the Jaccard similarity of two strings (0.0 – 1.0)."""
    tokens_a = _tokenize(a)
    tokens_b = _tokenize(b)
    if not tokens_a and not tokens_b:
        return 1.0
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


# ---------------------------------------------------------------------------
# Hybrid Engine
# ---------------------------------------------------------------------------


class HybridEngine:
    """Merges static-analysis and AI-analysis results into a unified list."""

    # Weights for the duplicate-detection score
    WEIGHT_LINE = 0.40
    WEIGHT_RULE = 0.30
    WEIGHT_DESC = 0.30

    # Threshold above which two issues are considered duplicates
    DUPLICATE_THRESHOLD = 0.70

    def __init__(self) -> None:
        self._counter = 0

    # -- public API ---------------------------------------------------------

    def normalize(
        self,
        issues: List[Dict[str, Any]],
        source: str,
    ) -> List[NormalizedIssue]:
        """Tag every issue with *source* and fill in missing optional fields.

        Parameters
        ----------
        issues : list[dict]
            Raw issue dicts as returned by ``StaticAnalyzer.analyze()`` or
            ``AIReviewer.review()``.
        source : str
            ``"Static"`` or ``"AI"``.
        """
        normalised: List[NormalizedIssue] = []
        for raw in issues:
            normalised.append(
                NormalizedIssue(
                    issue_id=self._generate_issue_id(),
                    severity=self._coerce_severity(raw.get("severity", "Low")),
                    line_number=int(raw.get("line_number", 0)),
                    description=str(raw.get("description", "")),
                    rule_type=str(raw.get("rule_type", "General")),
                    source=source,
                    ai_explanation=raw.get("ai_explanation"),
                    suggestion=raw.get("suggestion"),
                    file=raw.get("file"),
                    match_score=raw.get("match_score"),
                )
            )
        return normalised

    def fuse(
        self,
        static_issues: List[NormalizedIssue],
        ai_issues: List[NormalizedIssue],
    ) -> List[Dict[str, Any]]:
        """Merge two normalised lists into a single deduplicated issue list.

        Returns a list of plain dicts ready for JSONB storage.  Each dict
        contains an ``issue_id`` and a ``source`` field.
        """
        merged: List[NormalizedIssue] = []
        used_static: set[int] = set()

        for ai_issue in ai_issues:
            best_idx: Optional[int] = None
            best_score = 0.0

            for idx, static_issue in enumerate(static_issues):
                if idx in used_static:
                    continue
                score = self._duplicate_score(static_issue, ai_issue)
                if score >= self.DUPLICATE_THRESHOLD and score > best_score:
                    best_score = score
                    best_idx = idx

            if best_idx is not None:
                # Merge: prefer AI's richer explanation but keep static rule_type
                # if the AI one is too generic or if the static one is explicitly 'Syntax'.
                static_match = static_issues[best_idx]
                
                ai_rule_lower = ai_issue.rule_type.lower()
                static_rule_lower = static_match.rule_type.lower()
                
                if ai_rule_lower in ("general", "", "bug", "bugs") or static_rule_lower == "syntax":
                    final_rule_type = static_match.rule_type
                else:
                    final_rule_type = ai_issue.rule_type
                
                merged_issue = NormalizedIssue(
                    issue_id=static_match.issue_id,  # keep the earlier ID
                    severity=self._pick_higher_severity(
                        static_match.severity, ai_issue.severity
                    ),
                    line_number=ai_issue.line_number or static_match.line_number,
                    description=ai_issue.description or static_match.description,
                    rule_type=final_rule_type,
                    source="Static + AI",
                    ai_explanation=ai_issue.ai_explanation,
                    suggestion=ai_issue.suggestion,
                    file=ai_issue.file or static_match.file,
                    match_score=best_score,
                )
                merged.append(merged_issue)
                used_static.add(best_idx)
            else:
                merged.append(ai_issue)

        # Append unmatched static issues
        for idx, static_issue in enumerate(static_issues):
            if idx not in used_static:
                merged.append(static_issue)

        # Sort: severity (Critical first), then line_number ascending
        merged.sort(key=lambda i: (_severity_key(i.severity), i.line_number))

        return [issue.to_dict() for issue in merged]

    # -- private helpers ----------------------------------------------------

    def _generate_issue_id(self) -> str:
        """Return the next sequential issue ID (``ISS-000001``, …)."""
        self._counter += 1
        return f"ISS-{self._counter:06d}"

    def _duplicate_score(self, a: NormalizedIssue, b: NormalizedIssue) -> float:
        """Compute a weighted similarity score between two issues.

        Returns a float between 0.0 and 1.0.

        Axes
        ----
        * Same ``line_number`` → 40 %
        * Same ``rule_type``   → 30 %  (case-insensitive)
        * Description textual overlap → 30 %  (Jaccard similarity)
        """
        # Line match (exact)
        line_score = 1.0 if (a.line_number == b.line_number and a.line_number != 0) else 0.0

        # Rule / category match (case-insensitive)
        rule_a = a.rule_type.lower()
        rule_b = b.rule_type.lower()
        
        # Treat Syntax and Bugs as highly overlapping since Gemini often classifies syntax errors as bugs
        syntax_bug_aliases = {"syntax", "bug", "bugs", "error", "errors"}
        if rule_a == rule_b:
            rule_score = 1.0
        elif rule_a in syntax_bug_aliases and rule_b in syntax_bug_aliases:
            rule_score = 1.0
        else:
            rule_score = 0.0

        # Description similarity (Jaccard)
        desc_score = _text_similarity(a.description, b.description)

        # Boost score if they are on the same line and one is a Syntax error, 
        # because any critical AI bug on the exact same line as a syntax error is almost certainly the syntax error itself.
        base_score = (
            self.WEIGHT_LINE * line_score
            + self.WEIGHT_RULE * rule_score
            + self.WEIGHT_DESC * desc_score
        )
        
        if line_score == 1.0 and ("syntax" in (rule_a, rule_b)):
            if a.severity.lower() in ("critical", "high") and b.severity.lower() in ("critical", "high"):
                return max(base_score, self.DUPLICATE_THRESHOLD + 0.05)
                
        return base_score

    @staticmethod
    def _coerce_severity(raw: str) -> str:
        """Normalise severity to title-case (``Critical``, ``High``, …)."""
        mapping = {
            "critical": "Critical",
            "high": "High",
            "medium": "Medium",
            "low": "Low",
        }
        return mapping.get(raw.strip().lower(), "Low")

    @staticmethod
    def _pick_higher_severity(a: str, b: str) -> str:
        """Return whichever severity is more severe."""
        if _severity_key(a) <= _severity_key(b):
            return a
        return b
