from .MySQLDataService import MySQLDataService
from models.orm_item import Item
from models.item import ItemCreate, ItemUpdate, CategoryType, TransactionType
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid


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


# --- Singleton Pattern ---
item_service = ItemDataService()

# --- Dependency injection ---
def get_item_service():
    return item_service