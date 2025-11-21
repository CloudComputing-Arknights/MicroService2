from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from models.orm_item import Category


class CategoryDataService:
    async def get_categories(self, db: AsyncSession, *, skip: int = 0, limit: int = 100) -> List[Category]:
        """get all the categories"""
        query = select(Category).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()


# --- Dependency injection ---
def get_category_service() -> CategoryDataService:
    return CategoryDataService()