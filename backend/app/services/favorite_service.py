from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.favorite import Favorite
from app.models.favorite_collection import FavoriteCollection
from app.models.review import Review


class FavoriteService:
    def __init__(self):
        pass

    async def create_collection(
        self, db: AsyncSession, user_id: UUID, name: str
    ) -> FavoriteCollection:
        collection = FavoriteCollection(user_id=user_id, name=name)
        db.add(collection)
        await db.commit()
        await db.refresh(collection)
        return collection

    async def get_collections(
        self, db: AsyncSession, user_id: UUID
    ) -> Sequence[FavoriteCollection]:
        stmt = select(FavoriteCollection).where(FavoriteCollection.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def update_collection(
        self, db: AsyncSession, collection_id: UUID, user_id: UUID, name: str
    ) -> Optional[FavoriteCollection]:
        stmt = select(FavoriteCollection).where(
            FavoriteCollection.id == collection_id,
            FavoriteCollection.user_id == user_id,
        )
        result = await db.execute(stmt)
        collection = result.scalars().first()
        if not collection:
            return None
        collection.name = name
        await db.commit()
        await db.refresh(collection)
        return collection

    async def delete_collection(
        self, db: AsyncSession, collection_id: UUID, user_id: UUID
    ) -> bool:
        stmt = select(FavoriteCollection).where(
            FavoriteCollection.id == collection_id,
            FavoriteCollection.user_id == user_id,
        )
        result = await db.execute(stmt)
        collection = result.scalars().first()
        if not collection:
            return False
        await db.delete(collection)
        await db.commit()
        return True

    async def get_or_create_default_collection(
        self, db: AsyncSession, user_id: UUID
    ) -> FavoriteCollection:
        """Get or create the default 'My Favorites' collection for a user."""
        stmt = select(FavoriteCollection).where(
            FavoriteCollection.user_id == user_id,
            FavoriteCollection.name == "My Favorites",
        )
        result = await db.execute(stmt)
        collection = result.scalars().first()
        if collection:
            return collection
        collection = FavoriteCollection(user_id=user_id, name="My Favorites")
        db.add(collection)
        await db.commit()
        await db.refresh(collection)
        return collection

    async def add_review_to_collection(
        self,
        db: AsyncSession,
        user_id: UUID,
        collection_id: Optional[UUID],
        review_id: UUID,
    ) -> Optional[Favorite]:
        # check review exists
        rev_stmt = select(Review).where(Review.id == review_id)
        rev_res = await db.execute(rev_stmt)
        if not rev_res.scalars().first():
            return None

        # If no collection specified, use the default collection
        if collection_id is None:
            default_col = await self.get_or_create_default_collection(db, user_id)
            collection_id = default_col.id

        fav_stmt = select(Favorite).where(
            Favorite.user_id == user_id, Favorite.review_id == review_id
        )
        fav_res = await db.execute(fav_stmt)
        fav = fav_res.scalars().first()

        if fav:
            fav.collection_id = collection_id
            await db.commit()
            await db.refresh(fav)
            return fav
        else:
            new_fav = Favorite(
                user_id=user_id, review_id=review_id, collection_id=collection_id
            )
            db.add(new_fav)
            await db.commit()
            await db.refresh(new_fav)
            return new_fav

    async def remove_review_from_collection(
        self, db: AsyncSession, user_id: UUID, review_id: UUID
    ) -> bool:
        stmt = select(Favorite).where(
            Favorite.user_id == user_id, Favorite.review_id == review_id
        )
        result = await db.execute(stmt)
        fav = result.scalars().first()
        if fav:
            await db.delete(fav)
            await db.commit()
            return True
        return False
