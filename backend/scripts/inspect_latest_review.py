import asyncio
import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config.database import async_session_maker, init_db
from app.models.review import Review
from app.models.language import Language
from app.main import app
from httpx import AsyncClient

async def main():
    await init_db()

    async with async_session_maker() as db:
        # Get the latest review
        stmt = select(Review).order_by(Review.created_at.desc()).limit(1)
        res = await db.execute(stmt)
        latest_review = res.scalars().first()

        if not latest_review:
            print("No reviews found in database.")
            return

        print("=== 1. DATABASE LAYER ===")
        print(f"Review ID: {latest_review.id}")
        print(f"Title: {latest_review.title}")
        print(f"Status: {latest_review.status}")
        
        # Check language_id
        lang_id_str = str(latest_review.language_id) if latest_review.language_id else "null"
        print(f"language_id: {lang_id_str}")

        # Check corresponding language row
        if latest_review.language_id:
            lang_stmt = select(Language).where(Language.id == latest_review.language_id)
            lang_res = await db.execute(lang_stmt)
            lang_obj = lang_res.scalars().first()
            if lang_obj:
                print(f"Joined Language Row - ID: {lang_obj.id}, Name: {lang_obj.name}")
            else:
                print("Joined Language Row - NOT FOUND (Orphaned language_id)")
        else:
            print("Joined Language Row - SKIPPED (language_id is null)")
            
        print("\nReview Metadata:")
        print(json.dumps(latest_review.review_metadata, indent=2))
        
        review_id = latest_review.id
        
        # We need a user token to make the API call. Let's just create a token for the user who owns this review.
        user_id = latest_review.user_id
        
        from app.utils.security import create_access_token
        token = create_access_token({"sub": str(user_id)})
        
        print("\n=== 2. BACKEND API LAYER ===")
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(f"/api/v1/reviews/{review_id}", headers={"Authorization": f"Bearer {token}"})
            
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print("API Response JSON:")
                print(json.dumps(data, indent=2))
                
                print("\nSpecific Checks:")
                print(f"\"language_id\": {data.get('language_id')}")
                print(f"\"language\": {data.get('language')}")
            else:
                print(f"Error: {response.text}")


if __name__ == "__main__":
    asyncio.run(main())
