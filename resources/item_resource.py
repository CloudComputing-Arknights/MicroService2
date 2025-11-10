from fastapi import APIRouter, Depends, HTTPException, status, Query, Response, Header, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from typing import List, Optional
from datetime import datetime

from framework.database import get_db, SessionLocal
from services.ItemDataService import get_item_service, ItemDataService
from services.JobDataService import get_job_service, JobDataService
from models.item import ItemCreate, ItemUpdate, ItemRead, CategoryType, TransactionType
from models.job import JobRead, JobStatus


def run_item_creation_task(
        job_id: UUID,
        item_in_dict: dict,
):
    """Create an item asynchronously"""
    db = SessionLocal()

    item_service = ItemDataService()
    job_service = JobDataService()

    try:
        job_service.update_job_status(
            db,
            job_id=job_id,
            status=JobStatus.RUNNING
        )
        # Create the item
        item_in_obj = ItemCreate(**item_in_dict)
        new_item = item_service.create(db=db, obj_in=item_in_obj)

        job_service.update_job_status(
            db,
            job_id=job_id,
            status=JobStatus.COMPLETED,
            result_item_id=new_item.item_UUID
        )
        print("!!!", new_item.item_UUID)

    except Exception as e:
        print(f"Task {job_id} failed: {e}")  # 记录日志
        job_service.update_job_status(
            db,
            job_id=job_id,
            status=JobStatus.FAILED,
            error_message=str(e)
        )
    finally:
        db.close()

router = APIRouter(
    prefix="/items",
    tags=["Items"]
)

# @router.post("/", response_model=ItemRead, status_code=201)
# def create_item(
#         item_in: ItemCreate,
#         db: Session = Depends(get_db),
#         item_service: ItemDataService = Depends(get_item_service)
# ) -> ItemRead:
#     """
#     Accept the request of creating a new item and create it asynchronously.
#     """
#     # To implement
#     item = item_service.create(db=db, obj_in=item_in, user_UUID=item_in.user_UUID)
#     return item

# ======================================== job endpoint ========================================
@router.post("/", response_model=JobRead, status_code=202)
def create_item(
        item_in: ItemCreate,
        response: Response,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db),
        job_service: JobDataService = Depends(get_job_service)
) -> JobRead:
    """
    Accept the request of creating a new item, return 202 and start a job to create it asynchronously.
    """
    job_id = uuid4()
    db_job = job_service.create_job(db=db, job_id=job_id)

    # Create the item asynchronously, use .dict here because pydantic model is not thread-safe
    background_tasks.add_task(
        run_item_creation_task,
        job_id=job_id,
        item_in_dict=item_in.model_dump(),
    )

    # Set Location in Header for client to check status of the job
    status_url = router.url_path_for("get_job_status", job_id=str(job_id))
    response.headers["Location"] = status_url

    return db_job


@router.get("/jobs/{job_id}", response_model=JobRead, name="get_job_status")
def get_job_status(
        job_id: UUID,
        response: Response,
        db: Session = Depends(get_db),
        job_service: JobDataService = Depends(get_job_service)
):
    """
    Polling for the status of an item asynchronously.
    """
    job = job_service.get_job(db=db, job_id=job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    if job.status == JobStatus.COMPLETED:
        item_url = router.url_path_for("get_item", item_id=str(job.item_UUID))
        response.headers["Location"] = item_url

    return job

# ======================================== Item Endpoint ========================================
@router.get("/", response_model=List[ItemRead])
def list_items(
        ids: Optional[List[UUID]] = Query(None, description="Filter by a list of item IDs", alias="id"),
        category: Optional[CategoryType] = Query(None, description="Filter by item's category"),
        transaction_type: Optional[TransactionType] = Query(None, description="Filter by item's transaction type"),
        skip: int = 0,
        limit: int = 10,
        db: Session = Depends(get_db),
        item_service: ItemDataService = Depends(get_item_service)
) -> List[ItemRead]:
    """
    Get a list of all items, with optional filtering.
    """
    items = item_service.get_multi_filtered(
        db=db,
        ids=ids,
        category=category,
        transaction_type=transaction_type,
        skip=skip,
        limit=limit
    )
    return items


@router.get("/{item_id}", response_model=ItemRead, name="get_item")
def get_item(
        item_id: UUID,
        response: Response,
        db: Session = Depends(get_db),
        item_service: ItemDataService = Depends(get_item_service)
):
    """Get a single item by its id."""
    item = item_service.get(db=db, id_=item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    # Add ETag to header of response
    etag_value = item.updated_at.isoformat()    # timestamp -> ISO string
    response.headers["ETag"] = f'"{etag_value}"'

    return item

@router.patch("/{item_id}", response_model=ItemRead)
def update_item(
        item_id: UUID,
        item_update: ItemUpdate,
        response: Response,
        if_match: str = Header(...),    # return 422 if missing Header
        db: Session = Depends(get_db),
        item_service: ItemDataService = Depends(get_item_service)
):
    """Partially update an item's information."""
    # Parse ETag
    try:
        raw_etag_value = if_match.strip('"')
        expected_updated_at = datetime.fromisoformat(raw_etag_value)    # ISO string -> datetime
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid If-Match header format. Expected an ISO 8601 timestamp string."
        )
    updated_item = item_service.update_with_lock(
        db=db,
        item_id=item_id,
        item_update=item_update,
        expected_updated_at=expected_updated_at
    )
    # If successfully updated, return ETag using new "updated_at"
    new_etag_value = updated_item.updated_at.isoformat()
    response.headers["ETag"] = f'"{new_etag_value}"'

    return updated_item


@router.delete("/{item_id}", status_code=204)
def delete_item(
        item_id: UUID,
        db: Session = Depends(get_db),
        item_service: ItemDataService = Depends(get_item_service)
        # current_user_id: UUID = Depends(get_current_user) # 真实情况
):
    """Delete an item."""
    # Check if the row exists
    db_item = item_service.get(db=db, id_=item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    item_service.delete(db=db, id_=item_id)
    return