from sqlalchemy.orm import Session
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional

from models.orm_job import Job
from models.job import JobStatus


class JobDataService:
    async def get_job(self, db: AsyncSession, job_id: UUID) -> Optional[Job]:
        """get job based on job id"""
        query = select(Job).where(Job.job_UUID == job_id)
        result = await db.execute(query)
        return result.scalars().first()

    async def create_job(self, db: AsyncSession, job_id: UUID) -> Job:
        """Create a new Job record whose initial status is PENDING"""
        db_job = Job(job_UUID=job_id, status=JobStatus.PENDING)
        db.add(db_job)
        await db.commit()
        await db.refresh(db_job)
        return db_job

    async def update_job_status(
            self,
            db: AsyncSession,
            job_id: UUID,
            status: JobStatus,
            result_item_id: Optional[UUID] = None,
            error_message: Optional[str] = None
    ):
        """Update the status of job based on job id"""
        db_job = await self.get_job(db, job_id)
        if db_job:
            db_job.status = status
            if result_item_id:
                db_job.item_UUID = result_item_id
            if error_message:
                db_job.error_message = error_message
            await db.commit()
            await db.refresh(db_job)
        return db_job


# --- Dependency injection ---
def get_job_service() -> JobDataService:
    return JobDataService()