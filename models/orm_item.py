import uuid
from sqlalchemy import Column, String, Float, DateTime, Enum, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import TypeDecorator, CHAR
from datetime import datetime

from framework.database import Base
from models.item import ConditionType, TransactionType


class GUID(TypeDecorator):
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(value)
        return value


# ----- Item Model -----
class Item(Base):
    __tablename__ = "items"
    item_UUID = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_UUID = Column(GUID(), nullable=False)
    # user_UUID = Column(GUID(), ForeignKey("users.user_UUID"), nullable=False)
    # owner = relationship("User", back_populates="items")
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    condition = Column(Enum(ConditionType), nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    price = Column(Float, nullable=False)
    address_UUID = Column(GUID(), nullable=True)
    category = Column(JSON, nullable=True)
    image_urls = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)