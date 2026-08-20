from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.config.settings import settings
from app.engine.providers.base import BaseAIProvider
from app.engine.providers.gemini_provider import GeminiProvider


class AIReviewer:
    """Facade for the AI Analysis Engine."""

    def __init__(self) -> None:
        self.provider: BaseAIProvider = self._get_provider()

    def _get_provider(self) -> BaseAIProvider:
        if settings.AI_PROVIDER.lower() == "gemini":
            return GeminiProvider()
        # Fallback to Gemini
        return GeminiProvider()

    async def review(
        self, original_code: str, static_issues: List[Dict[str, Any]]
    ) -> Tuple[str, str, List[Dict[str, Any]], Any]:
        """Perform an AI code review using the configured provider."""
        return await self.provider.analyze_code(original_code, static_issues)
