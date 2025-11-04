from .AbstractBaseDataService import AbstractBaseDataService, ModelType, CreateSchemaType, UpdateSchemaType
from sqlalchemy.orm import Session
from typing import Any, List, Generic, Type
from pydantic import BaseModel


class MySQLDataService(AbstractBaseDataService[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        :param model: a SQLAlchemy model class
        """
        self.model = model

    def get(self, db: Session, id_: Any) -> ModelType | None:
        """
        Get a single row by primary key
        """
        return db.get(self.model, id_)

    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        Get pagination rows
        """
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType, **kwargs) -> ModelType:
        """
        Create a new row
        """
        obj_in_data = obj_in.model_dump()    # Pydantic model -> dict
        obj_in_data.update(kwargs)  # Add information in kwargs to data

        db_obj = self.model(**obj_in_data)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
            self,
            db: Session,
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
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, *, id_: Any) -> ModelType | None:
        """
        Delete a row by primary key
        """
        obj = db.get(self.model, id_)
        if obj:
            db.delete(obj)
            db.commit()
        return obj