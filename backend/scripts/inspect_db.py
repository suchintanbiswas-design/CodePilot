import asyncio
from sqlalchemy import select
from app.config.database import async_session_maker
from app.models.review import Review
from app.models.language import Language
import json

async def inspect():
    async with async_session_maker() as db:
        print("=== DATABASE INSPECTION ===")
        # 1. Check if languages exist
        lang_stmt = select(Language)
        lang_res = await db.execute(lang_stmt)
        langs = lang_res.scalars().all()
        print(f"Total seeded languages: {len(langs)}")
        for l in langs:
            print(f" - {l.name} (id: {l.id})")
            
        print("\n=== LATEST REVIEWS ===")
        stmt = select(Review).order_by(Review.created_at.desc()).limit(3)
        res = await db.execute(stmt)
        reviews = res.scalars().all()
        
        if not reviews:
            print("No reviews found.")
            return
            
        for r in reviews:
            print(f"\nReview: {r.id}")
            print(f"Title: {r.title}")
            print(f"Status: {r.status}")
            print(f"Language ID (raw DB): {r.language_id}")
            
            if r.language_id:
                l_stmt = select(Language).where(Language.id == r.language_id)
                l_res = await db.execute(l_stmt)
                l_obj = l_res.scalars().first()
                print(f"Joined Language: {l_obj.name if l_obj else 'ORPHAN/NOT FOUND'}")
            else:
                print("Joined Language: NULL")
                
            print(f"Metadata requested_language: {r.review_metadata.get('requested_language')}")
            
            # Use Pydantic to serialize this exact object just to be 100% sure
            print("\n  Pydantic Serialization Test:")
            from sqlalchemy.orm import selectinload
            stmt2 = select(Review).options(selectinload(Review.language)).where(Review.id == r.id)
            res2 = await db.execute(stmt2)
            loaded = res2.scalars().first()
            
            from app.schemas.review import ReviewResponse
            try:
                resp = ReviewResponse.model_validate(loaded)
                d = resp.model_dump(by_alias=True)
                print(f"  resp.language = {d.get('language')}")
            except Exception as e:
                print(f"  Serialization Error: {e}")
            
            print("-" * 40)

if __name__ == "__main__":
    asyncio.run(inspect())
