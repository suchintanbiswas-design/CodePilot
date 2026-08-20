from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.middleware.auth import get_current_user
from app.services.favorite_service import FavoriteService

router = APIRouter(prefix="/favorites", tags=["Favorites"])
favorite_service = FavoriteService()


@router.post("/collections")
async def create_collection(
    name: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    col = await favorite_service.create_collection(db, current_user.id, name)
    return {"success": True, "data": {"id": col.id, "name": col.name}}


@router.get("/collections")
async def get_collections(
    current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import func as sa_func, select as sa_select
    from app.models.favorite import Favorite

    cols = await favorite_service.get_collections(db, current_user.id)

    # Count favorites per collection
    counts = {}
    if cols:
        col_ids = [c.id for c in cols]
        count_stmt = (
            sa_select(Favorite.collection_id, sa_func.count())
            .where(Favorite.collection_id.in_(col_ids))
            .group_by(Favorite.collection_id)
        )
        count_res = await db.execute(count_stmt)
        counts = {row[0]: row[1] for row in count_res.all()}

    return {
        "success": True,
        "data": [
            {
                "id": c.id,
                "name": c.name,
                "count": counts.get(c.id, 0),
                "color": "bg-blue-500",
            }
            for c in cols
        ],
    }


@router.get("/collections/{collection_id}/reviews")
async def get_collection_reviews(
    collection_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

    from app.models.favorite import Favorite
    from app.models.review import Review

    stmt = (
        select(Review)
        .join(Favorite, Favorite.review_id == Review.id)
        .where(
            Favorite.collection_id == collection_id, Favorite.user_id == current_user.id
        )
    )
    result = await db.execute(stmt)
    reviews = result.scalars().all()
    # Return ReviewSummary-compatible shape for frontend rendering
    return {
        "success": True,
        "data": [
            {
                "id": r.id,
                "repositoryUrl": r.repo_url or r.title or "Unknown",
                "branch": "main",
                "status": r.status,
                "overallScore": (r.review_metadata or {}).get("quality_score", r.quality_score or 0),
                "issuesFound": len(r.issues) if r.issues else 0,
                "criticalIssues": len([i for i in (r.issues or []) if i.get("severity") == "Critical"]),
                "createdAt": r.created_at.isoformat() if r.created_at else "",
            }
            for r in reviews
        ],
    }


@router.put("/collections/{collection_id}")
async def update_collection(
    collection_id: UUID,
    name: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    col = await favorite_service.update_collection(
        db, collection_id, current_user.id, name
    )
    if not col:
        raise HTTPException(404, "Collection not found")
    return {"success": True, "data": {"id": col.id, "name": col.name}}


@router.delete("/collections/{collection_id}")
async def delete_collection(
    collection_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    success = await favorite_service.delete_collection(
        db, collection_id, current_user.id
    )
    if not success:
        raise HTTPException(404, "Collection not found")
    return {"success": True, "message": "Deleted"}


@router.post("/reviews/{review_id}")
async def add_review_to_collection(
    review_id: UUID,
    collection_id: UUID = None,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    fav = await favorite_service.add_review_to_collection(
        db, current_user.id, collection_id, review_id
    )
    if not fav:
        raise HTTPException(400, "Could not add to favorites")
    return {"success": True, "data": {"id": fav.id}}


@router.delete("/reviews/{review_id}")
async def remove_review_from_collection(
    review_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    success = await favorite_service.remove_review_from_collection(
        db, current_user.id, review_id
    )
    if not success:
        raise HTTPException(404, "Favorite not found")
    return {"success": True, "message": "Removed from favorites"}


@router.put("/reviews/{review_id}/move")
async def move_review_to_collection(
    review_id: UUID,
    collection_id: UUID = None,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    fav = await favorite_service.add_review_to_collection(
        db, current_user.id, collection_id, review_id
    )
    if not fav:
        raise HTTPException(400, "Could not move review")
    return {"success": True, "data": {"id": fav.id, "collection_id": fav.collection_id}}


@router.delete("/collections/{collection_id}/reviews/{review_id}")
async def remove_review_from_specific_collection(
    collection_id: UUID,
    review_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a review from a specific collection (used by FavoritesPage)."""
    success = await favorite_service.remove_review_from_collection(
        db, current_user.id, review_id
    )
    if not success:
        raise HTTPException(404, "Favorite not found")
    return {"success": True, "message": "Removed from favorites"}
