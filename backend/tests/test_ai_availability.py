import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import uuid
import json
from app.models.review import Review
from app.engine.providers.base import AIAvailabilityError
from app.services.review_service import ReviewService
from app.config.settings import settings
from app.engine.providers.gemini_provider import GeminiProvider
import dataclasses

def test_gemini_model_configuration():
    assert settings.GEMINI_MODEL == "gemini-3.5-flash-lite", "The configured model must be gemini-3.5-flash-lite"
    
@pytest.mark.asyncio
async def test_gemini_provider_response_parsing():
    provider = GeminiProvider()
    
    # Mocking the google genai response
    @dataclasses.dataclass
    class MockUsageMetadata:
        prompt_token_count: int = 150
        candidates_token_count: int = 200
        total_token_count: int = 350

    @dataclasses.dataclass
    class MockResponse:
        text: str = '{"ai_summary": "Great code", "improved_code": "def test(): return True", "ai_enhanced_issues": []}'
        usage_metadata: MockUsageMetadata = dataclasses.field(default_factory=MockUsageMetadata)

    provider.client = MagicMock()
    provider.client.aio.models.generate_content = AsyncMock(return_value=MockResponse())
    
    summary, improved, issues, usage = await provider.analyze_code("def test(): pass", [])
    
    assert summary == "Great code"
    assert improved == "def test(): return True"
    assert issues == []
    assert usage["model"] == "gemini-3.5-flash-lite"
    assert usage["input_tokens"] == 150
    assert usage["output_tokens"] == 200
    assert usage["total_tokens"] == 350
    
    # Verify the model was passed to the client correctly
    provider.client.aio.models.generate_content.assert_called_once()
    call_kwargs = provider.client.aio.models.generate_content.call_args.kwargs
    assert call_kwargs["model"] == "gemini-3.5-flash-lite"

@pytest.mark.asyncio
async def test_gemini_success():
    service = ReviewService(review_repo=MagicMock())
    review = Review(id=uuid.uuid4(), title="Test Success", source_code="def test(): pass", review_metadata={"requested_language": "Python"})
    
    with patch("app.engine.ai_reviewer.AIReviewer.review", new_callable=AsyncMock) as mock_review, \
         patch("app.engine.syntax_validator.SyntaxValidator.validate") as mock_syntax, \
         patch("app.engine.static_analyzer.StaticAnalyzer.analyze") as mock_static, \
         patch("app.engine.language_detector.LanguageDetector.validate_language") as mock_lang:
        
        mock_lang.return_value = {"detected_language": "Python", "confidence": 0}
        
        mock_syntax.return_value = [{"line_number": 1, "description": "Syntax ok"}]
        mock_static.return_value = [{"line_number": 1, "description": "Static ok"}]
        
        mock_review.return_value = (
            "AI Summary",
            "def test():\n    return True",
            [{"severity": "High", "description": "AI issue"}],
            None
        )
        
        db = AsyncMock()
        await service._process_single_file(db, review)
        
        assert review.review_metadata["ai_status"] == "available"
        assert "ai_unavailable_reason" not in review.review_metadata
        assert review.improved_code == "def test():\n    return True"
        # Should have fused issues
        assert len(review.issues) > 0
        
        # When Gemini succeeds and matches (or just returns an issue), 
        # the hybrid engine should assign AI or Static + AI
        has_ai_source = any("AI" in issue.get("source", "") for issue in review.issues)
        assert has_ai_source, "Expected at least one issue with an AI source"

@pytest.mark.asyncio
async def test_gemini_rate_limit():
    service = ReviewService(review_repo=MagicMock())
    review = Review(id=uuid.uuid4(), title="Test Rate Limit", source_code="def test(): pass", review_metadata={"requested_language": "Python"})
    
    with patch("app.engine.ai_reviewer.AIReviewer.review", new_callable=AsyncMock) as mock_review, \
         patch("app.engine.syntax_validator.SyntaxValidator.validate") as mock_syntax, \
         patch("app.engine.static_analyzer.StaticAnalyzer.analyze") as mock_static, \
         patch("app.engine.language_detector.LanguageDetector.validate_language") as mock_lang:
        
        mock_lang.return_value = {"detected_language": "Python", "confidence": 0}
        
        mock_syntax.return_value = [{"line_number": 1, "description": "Syntax ok", "severity": "Low", "rule_type": "Syntax"}]
        mock_static.return_value = [{"line_number": 1, "description": "Static ok", "severity": "Low", "rule_type": "Style"}]
        
        mock_review.side_effect = AIAvailabilityError("rate_limit", "Gemini API error: 429 Too Many Requests")
        
        db = AsyncMock()
        await service._process_single_file(db, review)
        
        assert review.review_metadata["ai_status"] == "unavailable"
        assert review.review_metadata["ai_unavailable_reason"] == "rate_limit"
        assert review.improved_code is None
        assert review.source_code == "def test(): pass"
        
        # Verify deterministic findings are preserved
        assert len(review.issues) > 0
        assert any(i["description"] == "Syntax ok" for i in review.issues)
        assert any(i["description"] == "Static ok" for i in review.issues)
        
        # Verify source tags are explicitly 'Static' and NOT 'AI' or 'Static + AI'
        for issue in review.issues:
            assert issue.get("source") == "Static"
            assert "AI" not in issue.get("source", "")
        
        # Verify scoreboard still runs
        assert "overall_quality" in review.review_metadata["scoring_engine"]

@pytest.mark.asyncio
async def test_gemini_provider_error():
    service = ReviewService(review_repo=MagicMock())
    review = Review(id=uuid.uuid4(), title="Test Provider Error", source_code="def test(): pass", review_metadata={"requested_language": "Python"})
    
    with patch("app.engine.ai_reviewer.AIReviewer.review", new_callable=AsyncMock) as mock_review, \
         patch("app.engine.syntax_validator.SyntaxValidator.validate") as mock_syntax, \
         patch("app.engine.static_analyzer.StaticAnalyzer.analyze") as mock_static, \
         patch("app.engine.language_detector.LanguageDetector.validate_language") as mock_lang:
        
        mock_lang.return_value = {"detected_language": "Python", "confidence": 0}
        
        mock_syntax.return_value = []
        mock_static.return_value = []
        
        mock_review.side_effect = AIAvailabilityError("provider_error", "Gemini API error: 500 Internal Server Error")
        
        db = AsyncMock()
        await service._process_single_file(db, review)
        
        assert review.review_metadata["ai_status"] == "unavailable"
        assert review.review_metadata["ai_unavailable_reason"] == "provider_error"
        assert review.improved_code is None
        assert review.source_code == "def test(): pass"
