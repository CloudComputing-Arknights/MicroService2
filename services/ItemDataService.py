from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import update
from typing import List, Optional
import uuid
from datetime import datetime

from .MySQLDataService import MySQLDataService
from models.orm_item import Item
from models.item import ItemCreate, ItemUpdate, CategoryType, TransactionType


class ItemDataService(MySQLDataService[Item, ItemCreate, ItemUpdate]):
    def __init__(self):
        super().__init__(model=Item)

    def get_multi_filtered(
            self,
            db: Session,
            *,
            category: Optional[CategoryType] = None,
            transaction_type: Optional[TransactionType] = None,
            skip: int = 0,
            limit: int = 100
    ) -> List[Item]:
        """
        Get filtered and paginated items.
        """
        query = db.query(self.model)

        if transaction_type:
            query = query.filter(self.model.transaction_type == transaction_type)
        if category:
            query = query.filter(self.model.category.contains(category))
        # Apply pagination
        return query.offset(skip).limit(limit).all()

    def get_by_user_id(self, db: Session, *, id_: uuid.UUID) -> List[Item]:
        """
        Get items by user id.
        """
        return db.query(self.model).filter(self.model.user_UUID == id_).all()

    def search_by_title(self, db: Session, *, title_keyword: str) -> List[Item]:
        """
        Search items by title.
        """
        return db.query(self.model).filter(self.model.title.ilike(f"%{title_keyword}%")).all()

    def update_with_lock(
            self,
            db: Session,
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

        result = db.execute(stmt)
        if result.rowcount == 0:
            exists = db.query(self.model.item_UUID).filter(self.model.item_UUID == item_id).first()
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

        db.commit()
        # Get updated item to get updated_at timestamp
        updated_item = self.get(db=db, id_=item_id)
        return updated_item

# --- Singleton Pattern ---
item_service = ItemDataService()

# --- Dependency injection ---
def get_item_service():
    return item_service