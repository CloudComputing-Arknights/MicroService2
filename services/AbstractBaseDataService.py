from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from typing import Any, List, TypeVar, Generic
from pydantic import BaseModel

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel) 


class AbstractBaseDataService(ABC, Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    @abstractmethod
    def get(self, db: Session, id_: Any) -> ModelType | None:
        raise NotImplementedError

    @abstractmethod
    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        raise NotImplementedError

    @abstractmethod
    def create(self, db: Session, *, obj_in: CreateSchemaType, **kwargs) -> ModelType:
        raise NotImplementedError

    @abstractmethod
    def update(
        self, 
        db: Session, 
        *, 
        db_obj: ModelType, 
        obj_in: UpdateSchemaType | dict[str, Any]
    ) -> ModelType:
        raise NotImplementedError

    @abstractmethod
    def delete(self, db: Session, *, id_: Any) -> ModelType | None:
        raise NotImplementedError