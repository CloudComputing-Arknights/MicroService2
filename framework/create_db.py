import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

from framework.database import Base
from framework.database import ASYNC_SQLALCHEMY_DATABASE_URL
# Import all ORM model so that they can be registered in Base.metadata
import models.orm_item
import models.orm_job

engine = create_async_engine(ASYNC_SQLALCHEMY_DATABASE_URL, echo=True)

async def init_db():
    print("Connecting to database and creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_db())