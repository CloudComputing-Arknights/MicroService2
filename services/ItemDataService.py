from os.path import exists
from fastapi import HTTPException, status
from sqlalchemy import update
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid
from datetime import datetime

from .MySQLDataService import MySQLDataService
from models.orm_item import Item, Category
from models.item import ItemCreate, ItemUpdate, TransactionType


class ItemDataService(MySQLDataService[Item, ItemCreate, ItemUpdate]):
    def __init__(self):
        super().__init__(model=Item)

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: ItemCreate,
        **kwargs
    ) -> Item:
        create_data = obj_in.model_dump()
        category_ids = create_data.pop("category_UUIDs", [])  # eject category ids from payload

        db_obj = self.model(**create_data)  # Create item po without category ids

        if category_ids:
            category_query = select(Category).where(Category.category_UUID.in_(category_ids))
            category_result = await db.execute(category_query)
            categories_to_link = category_result.scalars().all()
            db_obj.categories = categories_to_link  # Handle item_category_link table during commit

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj, attribute_names=['categories'])

        # Just in case if refresh didn't set relationship, manually set it
        if not db_obj.categories and category_ids:
            db_obj.categories = categories_to_link

        return db_obj

    async def get_multi_filtered(
            self,
            db: AsyncSession,
            *,
            ids: Optional[List[uuid.UUID]] = None,
            category_id: Optional[List[uuid.UUID]] = None,
            transaction_type: Optional[TransactionType] = None,
            title_search: Optional[str] = None,
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
        if category_id:
            query = query.where(self.model.categories.any(Category.category_UUID == category_id))
        if title_search:
            query = query.where(self.model.title.ilike(f"%{title_search}%"))
        # Apply pagination
        query = query.order_by(self.model.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().unique().all()

    # async def get_by_user_id(self, db: AsyncSession, *, id_: uuid.UUID) -> List[Item]:
    #     """
    #     Get items by user id.
    #     """
    #     query = select(self.model).where(self.model.user_id == id_)
    #     result = await db.execute(query)
    #     return result.scalars().all()

    async def search_by_title(self, db: AsyncSession, *, title_keyword: str) -> List[Item]:
        """
        Search items by title.
        """
        query = select(self.model).where(self.model.title.ilike(f"%{title_keyword}%"))
        result = await db.execute(query)
        return result.scalars().all()

    # async def update_with_lock(
    #         self,
    #         db: AsyncSession,
    #         *,
    #         item_id: uuid.UUID,
    #         item_update: ItemUpdate,
    #         expected_updated_at: datetime
    # ) -> Item:
    #     """
    #     Update an item based on updated_at.
    #     """
    #     update_data = item_update.model_dump(exclude_unset=True)
    #
    #     # Check item_UUID and updated_at
    #     stmt = (
    #         update(self.model)
    #         .where(
    #             self.model.item_UUID == item_id,
    #             self.model.updated_at == expected_updated_at
    #         )
    #         .values(**update_data)
    #     )
    #
    #     result = await db.execute(stmt)
    #     if result.rowcount == 0:
    #         exists_query = select(self.model.item_UUID).where(self.model.item_UUID == item_id)
    #         exists_result = await db.execute(exists_query)
    #         exists = exists_result.scalars().first()
    #         if not exists:  # Item doesn't exist (404)
    #             raise HTTPException(
    #                 status_code=status.HTTP_404_NOT_FOUND,
    #                 detail="Item not found"
    #             )
    #         else:   # Item exists but doesn't match updated_at (412)
    #             raise HTTPException(
    #                 status_code=status.HTTP_412_PRECONDITION_FAILED,
    #                 detail="Resource has been modified by another request. Please refresh and try again."
    #             )
    #
    #     await db.commit()
    #     # Get updated item to get updated_at timestamp
    #     updated_item = await self.get(db=db, id_=item_id)
    #     return updated_item

    async def update_with_lock(
            self,
            db: AsyncSession,
            *,
            item_id: uuid.UUID,
            item_update: ItemUpdate,
            expected_updated_at: datetime
    ) -> Item:
        """
        Update an item using 'SELECT FOR UPDATE' to lock the row
        and manually check the 'updated_at' timestamp for optimistic concurrency.

        This method IS capable of updating the 'categories' relationship.
        """
        # Lock the row
        query = (
            select(self.model)
            .where(self.model.item_UUID == item_id)
            .options(selectinload(self.model.categories))  # 确保加载了 categories
            .with_for_update()
        )

        result = await db.execute(query)
        db_obj = result.scalars().first()

        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )

        # ETag
        if db_obj.updated_at != expected_updated_at:
            raise HTTPException(
                status_code=status.HTTP_412_PRECONDITION_FAILED,
                detail="Resource has been modified by another request. Please refresh and try again."
            )

        # Exclude 'category_UUIDs' as it's a relation instead of columns
        update_data = item_update.model_dump(
            exclude_unset=True,
            exclude={"category_UUIDs"}
        )
        for key, value in update_data.items():
            setattr(db_obj, key, value)

        # Update category
        if "category_UUIDs" in item_update.model_fields_set:
            new_category_ids = item_update.category_UUIDs

            if not new_category_ids:
                db_obj.categories.clear()
            else:
                category_query = select(Category).where(
                    Category.category_UUID
                    .in_(new_category_ids)
                )
                category_result = await db.execute(category_query)
                new_categories = category_result.scalars().all()

                # Check whether IDs are available
                if len(new_categories) != len(new_category_ids):
                    pass

                db_obj.categories = new_categories

        await db.commit()
        await db.refresh(db_obj, ["categories"])

        return db_obj


# --- Singleton Pattern ---
item_service = ItemDataService()

# --- Dependency injection ---
def get_item_service():
    return item_service