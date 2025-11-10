from .AbstractBaseDataService import AbstractBaseDataService, ModelType, CreateSchemaType, UpdateSchemaType
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, List, Generic, Type
from pydantic import BaseModel


class MySQLDataService(AbstractBaseDataService[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        :param model: a SQLAlchemy model class
        """
        self.model = model

    async def get(self, db: AsyncSession, id_: Any) -> ModelType | None:
        """
        Get a single row by primary key
        """
        return await db.get(self.model, id_)

    async def get_multi(self, db: AsyncSession, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        Get pagination rows
        """
        query = select(self.model).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType, **kwargs) -> ModelType:
        """
        Create a new row
        """
        obj_in_data = obj_in.model_dump()    # Pydantic model -> dict
        obj_in_data.update(kwargs)  # Add information in kwargs to data

        db_obj = self.model(**obj_in_data)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
            self,
            db: AsyncSession,
            *,
            db_obj: ModelType,
            obj_in: UpdateSchemaType | dict[str, Any]
    ) -> ModelType:
        if isinstance(obj_in, BaseModel):
            update_data = obj_in.model_dump(exclude_unset=True)
        else:
            update_data = obj_in

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id_: Any) -> ModelType | None:
        """
        Delete a row by primary key
        """
        obj = await db.get(self.model, id_)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj