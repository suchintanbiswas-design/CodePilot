from datetime import datetime, timedelta
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.middleware.auth import get_current_user
from app.models.review import Review
from app.models.language import Language
from app.models.user import User
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])
user_service = UserService()


@router.get("/me/profile")
async def get_profile(
    current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    user = await user_service.get_profile(db, current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # --- Fetch all user reviews for stats ---
    stmt = select(Review).where(Review.user_id == current_user.id)
    result = await db.execute(stmt)
    reviews = result.scalars().all()

    # Total completed reviews
    completed = [r for r in reviews if r.status == "completed"]
    total_reviews = len(completed)

    # Average quality score
    scores = [r.quality_score for r in completed if r.quality_score is not None]
    avg_score = round(sum(scores) / len(scores)) if scores else 0

    # Repos reviewed (reviews with a repo_url)
    repos_reviewed = len([r for r in completed if r.repo_url])

    # Top languages from actual reviews
    lang_ids = [r.language_id for r in completed if r.language_id]
    lang_counts = Counter(lang_ids)
    top_languages = []
    if lang_counts:
        lang_stmt = select(Language).where(Language.id.in_(list(lang_counts.keys())))
        lang_result = await db.execute(lang_stmt)
        lang_map = {l.id: l.name for l in lang_result.scalars().all()}
        sorted_langs = lang_counts.most_common(6)
        for lid, count in sorted_langs:
            top_languages.append(lang_map.get(lid, "Unknown"))

    # Activity heatmap - last 365 days of review counts per day
    now = datetime.utcnow()
    one_year_ago = now - timedelta(days=365)
    activity = {}
    for r in reviews:
        if r.created_at and r.created_at >= one_year_ago:
            day_key = r.created_at.strftime("%Y-%m-%d")
            activity[day_key] = activity.get(day_key, 0) + 1

    return {
        "success": True,
        "data": {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "fullName": user.full_name,
            "role": user.role,
            "bio": user.bio,
            "avatarUrl": user.avatar_url,
            "githubProfile": user.github_profile,
            "linkedinProfile": user.linkedin_profile,
            "preferredLanguages": user.preferred_languages,
            "createdAt": user.created_at.isoformat() if user.created_at else None,
            "stats": {
                "totalReviews": total_reviews,
                "avgScore": avg_score,
                "reposReviewed": repos_reviewed,
                "topLanguages": top_languages,
            },
            "activity": activity,
        },
    }


@router.put("/me/profile")
async def update_profile(
    update_data: dict,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await user_service.update_profile(db, current_user.id, update_data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "success": True,
        "data": {
            "id": str(user.id),
            "fullName": user.full_name,
            "bio": user.bio,
            "githubProfile": user.github_profile,
            "linkedinProfile": user.linkedin_profile,
        },
    }


@router.get("/me/preferences")
async def get_preferences(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.settings import UserSettings
    stmt = select(UserSettings).where(UserSettings.user_id == current_user.id)
    result = await db.execute(stmt)
    settings = result.scalars().first()
    return {"success": True, "data": settings.preferences if settings else {}}


@router.put("/me/preferences")
async def update_preferences(
    preferences_data: dict,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    preferences = await user_service.update_preferences(db, current_user.id, preferences_data)
    return {"success": True, "data": preferences}


@router.put("/me/password")
async def update_password(
    password_data: dict,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    current_password = password_data.get("current_password")
    new_password = password_data.get("new_password")
    
    if not current_password or not new_password:
        raise HTTPException(status_code=400, detail="Missing current or new password")
        
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
        
    success = await user_service.change_password(
        db, current_user.id, current_password, new_password
    )
    if not success:
        raise HTTPException(status_code=400, detail="Invalid current password or update failed")
        
    return {"success": True, "message": "Password updated successfully"}


@router.get("/me/export")
def export_data(
    current_user=Depends(get_current_user),
):
    data = user_service.export_user_data(current_user)
    return Response(content=data, media_type="application/json")


@router.delete("/me")
async def delete_account(
    current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    success = await user_service.delete_account(db, current_user.id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete account")
    return {"success": True, "message": "Account deleted successfully"}
