from __future__ import annotations

from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.favorite import Favorite
from app.models.favorite_collection import FavoriteCollection
from app.models.language import Language
from app.models.review import Review


class ReviewRepository:
    """Repository for Review model."""

    def __init__(self) -> None:
        pass

    async def get(self, db: AsyncSession, id: UUID) -> Optional[Review]:
        stmt = select(Review).where(Review.id == id)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_with_relations(self, db: AsyncSession, id: UUID) -> Optional[Review]:
        stmt = (
            select(Review)
            .options(selectinload(Review.user), selectinload(Review.language))
            .where(Review.id == id)
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_paginated_by_user(
        self, db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 10
    ) -> Sequence[Review]:
        stmt = (
            select(Review)
            .options(selectinload(Review.language))
            .where(Review.user_id == user_id)
            .order_by(Review.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def count_by_user(self, db: AsyncSession, user_id: UUID) -> int:
        stmt = select(func.count()).where(Review.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one() or 0

    async def search_reviews(
        self,
        db: AsyncSession,
        user_id: UUID,
        query: Optional[str] = None,
        security_score_min: Optional[int] = None,
        maintainability_grade: Optional[str] = None,
        tech_debt_max: Optional[int] = None,
        ai_confidence_min: Optional[float] = None,
        skip: int = 0,
        limit: int = 10,
    ) -> Sequence[Review]:
        stmt = (
            select(Review)
            .options(selectinload(Review.language))
            .where(Review.user_id == user_id)
        )

        # Smart Filters via metadata_ (JSONB)
        if security_score_min is not None:
            stmt = stmt.where(
                Review.metadata_["security_score"].astext.cast(func.integer)
                >= security_score_min
            )
        if maintainability_grade is not None:
            stmt = stmt.where(
                Review.metadata_["maintainability_grade"].astext
                == maintainability_grade
            )
        if tech_debt_max is not None:
            stmt = stmt.where(
                Review.metadata_["tech_debt"].astext.cast(func.integer) <= tech_debt_max
            )
        if ai_confidence_min is not None:
            stmt = stmt.where(
                Review.metadata_["ai_confidence"].astext.cast(func.float)
                >= ai_confidence_min
            )

        # Global Search
        if query:
            search_term = f"%{query}%"
            stmt = (
                stmt.outerjoin(Language)
                .outerjoin(Favorite)
                .outerjoin(
                    FavoriteCollection, Favorite.collection_id == FavoriteCollection.id
                )
            )
            stmt = stmt.where(
                or_(
                    Review.title.ilike(search_term),
                    Review.repo_url.ilike(search_term),
                    Language.name.ilike(search_term),
                    FavoriteCollection.name.ilike(search_term),
                )
            )

        stmt = stmt.order_by(Review.created_at.desc()).offset(skip).limit(limit)

        # Performance: avoid Cartesian product duplicates with multiple joins and load relationships efficiently
        stmt = stmt.distinct()

        result = await db.execute(stmt)
        return result.scalars().all()

    async def create(self, db: AsyncSession, review: Review) -> Review:
        db.add(review)
        await db.commit()
        await db.refresh(review)
        return review

    async def delete(self, db: AsyncSession, id: UUID) -> None:
        stmt = select(Review).where(Review.id == id)
        result = await db.execute(stmt)
        review = result.scalars().first()
        if review:
            await db.delete(review)
            await db.commit()
