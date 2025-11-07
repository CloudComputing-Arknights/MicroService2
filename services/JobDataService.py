from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from models.orm_job import Job
from models.job import JobStatus


class JobDataService:
    def get_job(self, db: Session, job_id: UUID) -> Optional[Job]:
        """get job based on job id"""
        return db.query(Job).filter(Job.job_UUID == job_id).first()

    def create_job(self, db: Session, job_id: UUID) -> Job:
        """Create a new Job record whose initial status is PENDING"""
        db_job = Job(job_UUID=job_id, status=JobStatus.PENDING)
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        return db_job

    def update_job_status(
            self,
            db: Session,
            job_id: UUID,
            status: JobStatus,
            result_item_id: Optional[UUID] = None,
            error_message: Optional[str] = None
    ):
        """Update the status of job based on job id"""
        db_job = self.get_job(db, job_id)
        if db_job:
            db_job.status = status
            if result_item_id:
                db_job.item_UUID = result_item_id
            if error_message:
                db_job.error_message = error_message
            db.commit()
            db.refresh(db_job)
        return db_job


# --- Dependency injection ---
def get_job_service() -> JobDataService:
    return JobDataService()