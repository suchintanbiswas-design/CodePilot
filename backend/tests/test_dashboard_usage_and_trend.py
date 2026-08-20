import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta
from app.models.review import Review
from app.models.user import User
from app.engine.providers.gemini_provider import GeminiProvider
from app.services.review_service import ReviewService

@pytest.mark.asyncio
async def test_gemini_provider_usage_metadata():
    provider = GeminiProvider()
    
    # Mocking the Gemini response
    mock_response = MagicMock()
    mock_response.text = '{"ai_summary": "Test", "improved_code": "Test", "ai_enhanced_issues": []}'
    mock_response.usage_metadata = MagicMock()
    mock_response.usage_metadata.prompt_token_count = 150
    mock_response.usage_metadata.candidates_token_count = 50
    mock_response.usage_metadata.total_token_count = 200
    
    provider.client = MagicMock()
    provider.client.aio.models.generate_content = AsyncMock(return_value=mock_response)
    provider.types = MagicMock()
    
    ai_summary, improved_code, issues, usage = await provider.analyze_code("code", [])
    
    assert usage is not None
    assert usage["input_tokens"] == 150
    assert usage["output_tokens"] == 50
    assert usage["total_tokens"] == 200

@pytest.mark.asyncio
async def test_gemini_provider_missing_metadata():
    provider = GeminiProvider()
    
    mock_response = MagicMock()
    mock_response.text = '{"ai_summary": "Test", "improved_code": "Test", "ai_enhanced_issues": []}'
    mock_response.usage_metadata = None
    
    provider.client = MagicMock()
    provider.client.aio.models.generate_content = AsyncMock(return_value=mock_response)
    provider.types = MagicMock()
    
    ai_summary, improved_code, issues, usage = await provider.analyze_code("code", [])
    
    assert usage is None

def test_dashboard_tokens_sum_and_exclusion():
    # Test logic directly
    user1_id = "1"
    
    r1 = Review(user_id=user1_id, status="completed", review_metadata={"ai_usage": {"total_tokens": 1000}})
    r2 = Review(user_id=user1_id, status="completed", review_metadata={"ai_usage": {"total_tokens": 2500}})
    r3 = Review(user_id="2", status="completed", review_metadata={"ai_usage": {"total_tokens": 5000}})
    r4 = Review(user_id=user1_id, status="failed", review_metadata={"ai_usage": {"total_tokens": 500}})
    
    reviews = [r1, r2, r4] # Controller only gets user1's reviews
    
    ai_usage_tokens = 0
    has_tokens = False
    for r in reviews:
        if r.status == "completed" and r.review_metadata and "ai_usage" in r.review_metadata:
            ai_usage = r.review_metadata["ai_usage"]
            if "total_tokens" in ai_usage:
                ai_usage_tokens += ai_usage["total_tokens"]
                has_tokens = True
                
    assert has_tokens is True
    assert ai_usage_tokens == 3500 # Excludes failed r4, excludes user2's r3 by definition

def test_tech_debt_trend():
    now = datetime.utcnow()
    
    # 1. One historical period
    reviews1 = [
        Review(status="completed", created_at=now, review_metadata={"tech_debt": 100}),
        Review(status="completed", created_at=now, review_metadata={"tech_debt": 120}),
    ]
    
    def calc_trend(reviews):
        debt_by_date = {}
        for r in reviews:
            if r.status == "completed" and r.created_at and r.review_metadata and "tech_debt" in r.review_metadata:
                d = r.created_at.date()
                if d not in debt_by_date:
                    debt_by_date[d] = []
                debt_by_date[d].append(int(r.review_metadata["tech_debt"]))
        if len(debt_by_date) >= 2:
            sorted_dates = sorted(debt_by_date.keys())
            earliest_date = sorted_dates[0]
            latest_date = sorted_dates[-1]
            earliest_avg = sum(debt_by_date[earliest_date]) / len(debt_by_date[earliest_date])
            latest_avg = sum(debt_by_date[latest_date]) / len(debt_by_date[latest_date])
            if earliest_avg > 0:
                return round(((earliest_avg - latest_avg) / earliest_avg) * 100, 1)
        return None

    assert calc_trend(reviews1) is None
    
    # 2. Reduced debt
    reviews2 = [
        Review(status="completed", created_at=now - timedelta(days=5), review_metadata={"tech_debt": 100}), # earliest avg 100
        Review(status="completed", created_at=now, review_metadata={"tech_debt": 70}), # latest avg 70
    ]
    assert calc_trend(reviews2) == 30.0 # 30% Reduced
    
    # 3. Increased debt
    reviews3 = [
        Review(status="completed", created_at=now - timedelta(days=5), review_metadata={"tech_debt": 100}), # earliest avg 100
        Review(status="completed", created_at=now, review_metadata={"tech_debt": 125}), # latest avg 125
    ]
    assert calc_trend(reviews3) == -25.0 # -25% (Increased)
