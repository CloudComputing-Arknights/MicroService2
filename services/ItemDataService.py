from os.path import exists
from fastapi import HTTPException, status
from sqlalchemy import update
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid
from datetime import datetime

from .MySQLDataService import MySQLDataService
from models.orm_item import Item
from models.item import ItemCreate, ItemUpdate, CategoryType, TransactionType


class ItemDataService(MySQLDataService[Item, ItemCreate, ItemUpdate]):
    def __init__(self):
        super().__init__(model=Item)

    async def get_multi_filtered(
            self,
            db: AsyncSession,
            *,
            ids: Optional[List[uuid.UUID]] = None,
            category: Optional[CategoryType] = None,
            transaction_type: Optional[TransactionType] = None,
            skip: int = 0,
            limit: int = 100
    ) -> List[Item]:
        """
        Get filtered and paginated items.
        """
        query = select(self.model)

        if ids:
            query = query.where(self.model.item_UUID.in_(ids))
        if transaction_type:
            query = query.where(self.model.transaction_type == transaction_type)
        if category:
            query = query.where(self.model.category.contains(category))
        # Apply pagination
        query = query.order_by(self.model.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_user_id(self, db: AsyncSession, *, id_: uuid.UUID) -> List[Item]:
        """
        Get items by user id.
        """
        query = select(self.model).where(self.model.user_id == id_)
        result = await db.execute(query)
        return result.scalars().all()

    async def search_by_title(self, db: AsyncSession, *, title_keyword: str) -> List[Item]:
        """
        Search items by title.
        """
        query = select(self.model).where(self.model.title.ilike(f"%{title_keyword}%"))
        result = await db.execute(query)
        return result.scalars().all()

    async def update_with_lock(
            self,
            db: AsyncSession,
            *,
            item_id: uuid.UUID,
            item_update: ItemUpdate,
            expected_updated_at: datetime
    ) -> Item:
        """
        Update an item based on updated_at.
        """
        update_data = item_update.model_dump(exclude_unset=True)

        # Check item_UUID and updated_at
        stmt = (
            update(self.model)
            .where(
                self.model.item_UUID == item_id,
                self.model.updated_at == expected_updated_at
            )
            .values(**update_data)
        )

        result = await db.execute(stmt)
        if result.rowcount == 0:
            exists_query = select(self.model.item_UUID).where(self.model.item_UUID == item_id)
            exists_result = await db.execute(exists_query)
            exists = exists_result.scalars().first()
            if not exists:  # Item doesn't exist (404)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Item not found"
                )
            else:   # Item exists but doesn't match updated_at (412)
                raise HTTPException(
                    status_code=status.HTTP_412_PRECONDITION_FAILED,
                    detail="Resource has been modified by another request. Please refresh and try again."
                )

        await db.commit()
        # Get updated item to get updated_at timestamp
        updated_item = await self.get(db=db, id_=item_id)
        return updated_item

# --- Singleton Pattern ---
item_service = ItemDataService()

# --- Dependency injection ---
def get_item_service():
    return item_service