from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, List, TypeVar, Generic
from pydantic import BaseModel

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel) 


class AbstractBaseDataService(ABC, Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    @abstractmethod
    async def get(self, db: Session, id_: Any) -> ModelType | None:
        raise NotImplementedError

    @abstractmethod
    async def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        raise NotImplementedError

    @abstractmethod
    async def create(self, db: Session, *, obj_in: CreateSchemaType, **kwargs) -> ModelType:
        raise NotImplementedError

    @abstractmethod
    async def update(
        self, 
        db: Session, 
        *, 
        db_obj: ModelType, 
        obj_in: UpdateSchemaType | dict[str, Any]
    ) -> ModelType:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, db: Session, *, id_: Any) -> ModelType | None:
        raise NotImplementedError