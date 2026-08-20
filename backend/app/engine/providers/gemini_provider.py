from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Tuple

from app.config.settings import settings
from app.engine.providers.base import BaseAIProvider

logger = logging.getLogger(__name__)


class GeminiProvider(BaseAIProvider):
    """Gemini-based AI Provider for code review."""

    def __init__(self) -> None:
        try:
            from google import genai
            from google.genai import types

            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            self.types = types
            logger.info(f"Gemini model configured: {settings.GEMINI_MODEL}")
        except ImportError:
            logger.warning("google-genai is not installed.")
            self.client = None

    async def analyze_code(
        self, original_code: str, static_issues: List[Dict[str, Any]]
    ) -> Tuple[str, str, List[Dict[str, Any]]]:
        if not self.client:
            return (
                "AI Analysis not available due to missing library.",
                original_code,
                static_issues,
            )

        prompt = (
            "You are an expert software engineer performing a code review. "
            "Please analyze the provided code and static analysis issues.\n\n"
            f"Original Code:\n{original_code}\n\n"
            f"Static Issues:\n{json.dumps(static_issues, indent=2)}\n\n"
            "Return a JSON object with the following structure exactly (do NOT include markdown wrapping like ```json):\n"
            "{\n"
            '  "ai_summary": "A high-level summary of the code quality and main issues.",\n'
            '  "improved_code": "The fully refactored original code with improvements applied. Keep the same language.",\n'
            '  "ai_enhanced_issues": [\n'
            "    {\n"
            '      "severity": "Critical|High|Medium|Low",\n'
            '      "line_number": 12,\n'
            '      "description": "Clear explanation of what is wrong",\n'
            '      "rule_type": "Bugs|Smells|Security...",\n'
            '      "ai_explanation": "Simple language explanation of why this is an issue and how to fix it."\n'
            "    }\n"
            "  ]\n"
            "}"
        )

        try:
            response = await self.client.aio.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config=self.types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )

            result_text = response.text
            data = json.loads(result_text)

            ai_summary = data.get("ai_summary", "No summary provided.")
            improved_code = data.get("improved_code", original_code)
            ai_enhanced_issues = data.get("ai_enhanced_issues", static_issues)
            
            usage_info = None
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                um = response.usage_metadata
                usage_info = {
                    "model": settings.GEMINI_MODEL,
                    "input_tokens": getattr(um, 'prompt_token_count', getattr(um, 'input_token_count', 0)),
                    "output_tokens": getattr(um, 'candidates_token_count', getattr(um, 'output_token_count', 0)),
                    "total_tokens": getattr(um, 'total_token_count', 0)
                }

            return ai_summary, improved_code, ai_enhanced_issues, usage_info
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            from app.engine.providers.base import AIAvailabilityError
            reason = "provider_error"
            # Check for rate limit indicators in the exception
            err_str = str(e).lower()
            if "429" in err_str or "resource_exhausted" in err_str or "too many requests" in err_str or "quota" in err_str:
                reason = "rate_limit"
            raise AIAvailabilityError(reason, f"Gemini API error: {e}")
