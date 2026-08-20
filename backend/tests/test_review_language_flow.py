import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_language_persistence_valid_language():
    """Valid language never falls back to Unknown. Continue Anyway -> final review language = Java."""
    from app.services.review_service import ReviewService
    from app.schemas.review import ReviewCreateRequest
    from app.models.language import Language
    
    db_mock = AsyncMock()
    java_id = uuid4()
    
    from unittest.mock import MagicMock
    # First call for Language
    scalar_mock_1 = MagicMock()
    scalar_mock_1.first.return_value = Language(id=java_id, name="Java")
    res_mock_1 = MagicMock()
    res_mock_1.scalars.return_value = scalar_mock_1
    
    # Second call for Review (eager loading)
    scalar_mock_2 = MagicMock()
    # We don't strictly need a fully formed Review here, just an object that has language_id
    # We will just return a mock Review that has the language_id set
    mock_review = MagicMock()
    mock_review.language_id = java_id
    mock_review.review_metadata = {"requested_language": "Java"}
    scalar_mock_2.first.return_value = mock_review
    res_mock_2 = MagicMock()
    res_mock_2.scalars.return_value = scalar_mock_2
    
    db_mock.execute.side_effect = [res_mock_1, res_mock_2]
    
    service = ReviewService(review_repo=None)
    req = ReviewCreateRequest(title="Test Java", language_id="Java", source_code="x=1")
    
    with patch("app.services.review_service.select") as mock_select:
        review = await service.submit_review(db_mock, uuid4(), req)
        
        # Verify language is correctly resolved
        assert review.language_id == java_id
        assert review.review_metadata.get("requested_language") == "Java"
        
        # Verify db.execute was called
        assert db_mock.execute.called

@pytest.mark.asyncio
async def test_language_persistence_switch_to_python():
    """Switch to Python -> final review language = Python."""
    from app.services.review_service import ReviewService
    from app.schemas.review import ReviewCreateRequest
    from app.models.language import Language
    
    db_mock = AsyncMock()
    python_id = uuid4()
    
    lang_mock = Language(id=python_id, name="Python")
    from unittest.mock import MagicMock
    
    # DB Call 1: Get Language name for language_id
    scalar_mock_1 = MagicMock()
    scalar_mock_1.first.return_value = lang_mock
    res_mock_1 = MagicMock()
    res_mock_1.scalars.return_value = scalar_mock_1
    
    # DB Call 2: Final refetch of the Review
    mock_review = MagicMock()
    mock_review.language_id = python_id
    mock_review.review_metadata = {"requested_language": str(python_id)}
    
    scalar_mock_2 = MagicMock()
    scalar_mock_2.first.return_value = mock_review
    res_mock_2 = MagicMock()
    res_mock_2.scalars.return_value = scalar_mock_2
    
    # x=1 is detected as Python/Unknown, so no switch query is executed.
    # Total calls: 1 (lookup language), 2 (refetch Review)
    db_mock.execute.side_effect = [res_mock_1, res_mock_2]
    
    service = ReviewService(review_repo=None)
    req = ReviewCreateRequest(title="Test Python", language_id=str(python_id), source_code="x=1")
    
    with patch("app.services.review_service.select") as mock_select:
        review = await service.submit_review(db_mock, uuid4(), req)
        
        assert review.language_id == python_id
        assert review.review_metadata.get("requested_language") == str(python_id)

@pytest.mark.asyncio
async def test_language_persistence_unknown_language():
    """Unknown is only returned when the language genuinely cannot be resolved."""
    from app.services.review_service import ReviewService
    from app.schemas.review import ReviewCreateRequest
    from unittest.mock import MagicMock
    
    db_mock = AsyncMock()
    req_lang_id = str(uuid4())
    
    mock_review = MagicMock()
    mock_review.language_id = None
    mock_review.review_metadata = {"requested_language": req_lang_id}
    
    # DB Call 1: Get Language (returns None)
    scalar_mock_1 = MagicMock()
    scalar_mock_1.first.return_value = None
    res_mock_1 = MagicMock()
    res_mock_1.scalars.return_value = scalar_mock_1
    
    # DB Call 2: Final refetch of the Review
    scalar_mock_2 = MagicMock()
    scalar_mock_2.first.return_value = mock_review
    res_mock_2 = MagicMock()
    res_mock_2.scalars.return_value = scalar_mock_2
    
    # x=1 is detected as Python/Unknown, so no switch query is executed.
    db_mock.execute.side_effect = [res_mock_1, res_mock_2]
    
    service = ReviewService(review_repo=None)
    req = ReviewCreateRequest(title="Test Unknown", language_id=req_lang_id, source_code="x=1")
    
    with patch("app.services.review_service.select") as mock_select:
        review = await service.submit_review(db_mock, uuid4(), req)
        
        assert review.language_id is None
        assert review.review_metadata.get("requested_language") == req.language_id

@pytest.mark.asyncio
async def test_auto_detect_language_success():
    """Submit code with no language -> detects Python -> sets final language to Python."""
    from app.services.review_service import ReviewService
    from app.models.review import Review
    from unittest.mock import MagicMock
    
    db_mock = AsyncMock()
    service = ReviewService(review_repo=None)
    
    # Mock Review
    review = Review(
        id=uuid4(),
        user_id=uuid4(),
        language_id=None,
        source_code="def foo(): pass",
        review_metadata={}
    )
    
    python_id = uuid4()
    
    with patch("app.engine.language_detector.LanguageDetector.validate_language") as mock_detect:
        mock_detect.return_value = {
            "detected_language": "Python",
            "confidence": 99,
            "evidence": ["def keyword"]
        }
        
        # Mock DB queries inside _process_single_file
        # 1. Update language_id (Language lookup for "Python")
        from app.models.language import Language
        scalar_mock_1 = MagicMock()
        scalar_mock_1.first.return_value = Language(id=python_id, name="Python")
        res_mock_1 = MagicMock()
        res_mock_1.scalars.return_value = scalar_mock_1
        
        db_mock.execute.side_effect = [res_mock_1]
        
        # Mock remaining pipeline dependencies
        service.syntax_validator = MagicMock()
        service.syntax_validator.validate.return_value = []
        service.static_analyzer = MagicMock()
        service.static_analyzer.analyze.return_value = []
        service.static_analyzer.calculate_cyclomatic_complexity.return_value = 1
        service.ai_reviewer = AsyncMock()
        service.ai_reviewer.review.return_value = ("Summary", "Code", [], {})
        service.confidence_engine = MagicMock()
        service.confidence_engine.calculate_all.return_value = []
        service.scoring_engine = MagicMock()
        service.scoring_engine.calculate_scores.return_value = {"overall_quality": 100}
        
        await service._process_single_file(db_mock, review)
        
        assert review.language_id == python_id
        assert review.review_metadata["language_detection"]["final_language"] == "Python"
        assert review.review_metadata["language_detection"]["language_switched"] is False

@pytest.mark.asyncio
async def test_auto_detect_language_low_confidence_fails():
    """Submit code with no language and low confidence -> throws Exception."""
    from app.services.review_service import ReviewService
    from app.models.review import Review
    
    db_mock = AsyncMock()
    service = ReviewService(review_repo=None)
    
    review = Review(
        id=uuid4(),
        user_id=uuid4(),
        language_id=None,
        source_code="x",
        review_metadata={}
    )
    
    with patch("app.engine.language_detector.LanguageDetector.validate_language") as mock_detect:
        mock_detect.return_value = {
            "detected_language": "Unknown",
            "confidence": 0,
            "evidence": []
        }
        
        with pytest.raises(Exception, match="Could not confidently determine programming language"):
            await service._process_single_file(db_mock, review)

