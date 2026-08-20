"""
Diagnostic script: reproduce the exact language persistence flow.
Run with: python scripts/debug_language_flow.py
"""
import asyncio
from uuid import uuid4

from sqlalchemy import select

from app.config.database import async_session_maker, init_db
from app.models.language import Language


async def main():
    await init_db()

    async with async_session_maker() as db:
        # 1. Show all seeded languages
        stmt = select(Language)
        res = await db.execute(stmt)
        langs = res.scalars().all()

        print("=== SEEDED LANGUAGES ===")
        for lang in langs:
            print(f"  id={lang.id}  name={lang.name!r}  ext={lang.extension!r}")
        print()

        if not langs:
            print("ERROR: No languages seeded! Run: python -m scripts.seed")
            return

        # 2. Simulate the exact lookup that submit_review does
        test_inputs = ["Python", "python", "Java", "java", "JavaScript"]
        for test_lang in test_inputs:
            stmt2 = select(Language).where(Language.name.ilike(test_lang))
            res2 = await db.execute(stmt2)
            found = res2.scalars().first()
            if found:
                print(f"  Lookup '{test_lang}' => FOUND: id={found.id}, name={found.name}")
            else:
                print(f"  Lookup '{test_lang}' => NOT FOUND (will become language_id=None)")

        print()
        
        # 3. Now check what the frontend is actually sending
        # The frontend sends language_id as the value from a <select> dropdown
        # What values does the dropdown use?
        print("=== FRONTEND FLOW ===")
        print("The frontend dropdown sends language_id as a STRING.")
        print("submit_review checks isinstance(req.language_id, str)")
        print("and does: Language.name.ilike(req.language_id)")
        print()
        print("If the frontend sends the language NAME (e.g., 'Python'), lookup works.")
        print("If the frontend sends the language UUID, Pydantic parses it as UUID,")
        print("and submit_review uses it directly as lang_id.")

        # 4. Check a review with language_id set
        from app.models.review import Review
        stmt3 = select(Review).order_by(Review.created_at.desc()).limit(5)
        res3 = await db.execute(stmt3)
        reviews = res3.scalars().all()

        print()
        print("=== LATEST 5 REVIEWS ===")
        for r in reviews:
            print(f"  id={r.id}")
            print(f"    language_id={r.language_id}")
            print(f"    status={r.status}")
            print(f"    metadata.requested_language={r.review_metadata.get('requested_language', 'NOT SET')}")
            lang_det = r.review_metadata.get('language_detection', {})
            print(f"    metadata.language_detection.selected={lang_det.get('selected_language', 'N/A')}")
            print(f"    metadata.language_detection.detected={lang_det.get('detected_language', 'N/A')}")
            print(f"    metadata.language_detection.is_match={lang_det.get('is_match', 'N/A')}")
            print()

        # 5. Test the Pydantic serialization with a real review that has language_id
        from sqlalchemy.orm import selectinload
        if reviews:
            latest = reviews[0]
            if latest.language_id:
                # Reload with relations
                stmt4 = (
                    select(Review)
                    .options(selectinload(Review.language))
                    .where(Review.id == latest.id)
                )
                res4 = await db.execute(stmt4)
                loaded = res4.scalars().first()

                print("=== PYDANTIC SERIALIZATION TEST ===")
                print(f"  review.language_id = {loaded.language_id}")
                print(f"  review.language = {loaded.language}")
                if loaded.language:
                    print(f"  review.language.name = {loaded.language.name}")
                    print(f"  review.language.id = {loaded.language.id}")
                else:
                    print("  review.language is None! This is the bug.")
                    print("  language_id is set but the Language row doesn't exist,")
                    print("  or the relationship isn't loading properly.")

                # Try serializing through ReviewResponse
                from app.schemas.review import ReviewResponse
                try:
                    resp = ReviewResponse.model_validate(loaded)
                    print(f"  ReviewResponse.language = {resp.language}")
                    print(f"  ReviewResponse.language_id = {resp.language_id}")
                    d = resp.model_dump(by_alias=True)
                    print(f"  JSON language = {d.get('language')}")
                    print(f"  JSON language_id = {d.get('language_id')}")
                except Exception as e:
                    print(f"  SERIALIZATION ERROR: {e}")
            else:
                print("=== Latest review has language_id=None ===")
                print("  This is why Language: Unknown appears.")
                print(f"  metadata.requested_language = {latest.review_metadata.get('requested_language', 'NOT SET')}")


asyncio.run(main())
