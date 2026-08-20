from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

class AIAvailabilityError(Exception):
    def __init__(self, reason: str, message: str):
        super().__init__(message)
        self.reason = reason


class BaseAIProvider(ABC):
    """Base class for AI Providers used in code review."""

    @abstractmethod
    async def analyze_code(
        self, original_code: str, static_issues: List[Dict[str, Any]]
    ) -> Tuple[str, str, List[Dict[str, Any]], Any]:
        """
        Analyze the code and static issues using AI.

        Args:
            original_code: The original source code to review.
            static_issues: A list of static issues found by the static analysis engine.

        Returns:
            A tuple of (ai_summary, improved_code, ai_enhanced_issues)
        """
        pass
