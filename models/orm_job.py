from sqlalchemy import Column, String, Enum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import TypeDecorator, CHAR
import uuid
from framework.database import Base
from models.job import JobStatus as JobStatusEnum


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


class Job(Base):
    __tablename__ = "jobs"

    job_UUID = Column(GUID(), primary_key=True, index=True)
    status = Column(Enum(JobStatusEnum), default=JobStatusEnum.PENDING, nullable=False)

    # UUID of the created item
    item_UUID = Column(GUID(), nullable=True)
    error_message = Column(String, nullable=True)