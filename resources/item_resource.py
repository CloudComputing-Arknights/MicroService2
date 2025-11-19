from fastapi import APIRouter, Depends, HTTPException, status, Query, Response, Header, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID, uuid4
from typing import List, Optional
from datetime import datetime

from framework.database import get_db, SessionLocal, AsyncSessionLocal
from services.ItemDataService import get_item_service, ItemDataService
from services.JobDataService import get_job_service, JobDataService
from models.item import ItemCreate, ItemUpdate, ItemRead, TransactionType
from models.job import JobRead, JobStatus


async def run_item_creation_task(
        job_id: UUID,
        item_in_dict: dict,
):
    """Create an item asynchronously"""
    async with AsyncSessionLocal() as db:
        item_service = ItemDataService()
        job_service = JobDataService()

        try:
            await job_service.update_job_status(
                db,
                job_id=job_id,
                status=JobStatus.RUNNING
            )

            item_in_obj = ItemCreate(**item_in_dict)
            new_item = await item_service.create(db=db, obj_in=item_in_obj)

            await job_service.update_job_status(
                db,
                job_id=job_id,
                status=JobStatus.COMPLETED,
                result_item_id=new_item.item_UUID
            )
            # print("!!!", new_item.item_UUID)

        except Exception as e:
            print(f"Task {job_id} failed: {e}")
            await job_service.update_job_status(
                db,
                job_id=job_id,
                status=JobStatus.FAILED,
                error_message=str(e)
            )

router = APIRouter(
    prefix="/items",
    tags=["Items"]
)

# ======================================== job endpoint ========================================
@router.post("/", response_model=JobRead, status_code=202)
async def create_item(
        item_in: ItemCreate,
        response: Response,
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_db),
        job_service: JobDataService = Depends(get_job_service)
) -> JobRead:
    """
    Accept the request of creating a new item, return 202 and start a job to create it asynchronously.
    """
    job_id = uuid4()
    db_job = await job_service.create_job(db=db, job_id=job_id)

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
async def get_job_status(
        job_id: UUID,
        response: Response,
        db: AsyncSession = Depends(get_db),
        job_service: JobDataService = Depends(get_job_service)
):
    """
    Polling for the status of an item asynchronously.
    """
    job = await job_service.get_job(db=db, job_id=job_id)

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
async def list_items(
        ids: Optional[List[UUID]] = Query(None, description="Filter by a list of item IDs", alias="id"),
        category_id: Optional[UUID] = Query(None, description="Filter by item's category id"),
        transaction_type: Optional[TransactionType] = Query(None, description="Filter by item's transaction type"),
        title_search: Optional[str] = Query(None, description="Search by item title (case-insensitive, partial match)", alias="search"),
        skip: int = 0,
        limit: int = 10,
        db: AsyncSession = Depends(get_db),
        item_service: ItemDataService = Depends(get_item_service)
) -> List[ItemRead]:
    """
    Get a list of all items, with optional filtering.
    """
    items = await item_service.get_multi_filtered(
        db=db,
        ids=ids,
        category_id=category_id,
        transaction_type=transaction_type,
        title_search=title_search,
        skip=skip,
        limit=limit
    )
    return items


@router.get("/{item_id}", response_model=ItemRead, name="get_item")
async def get_item(
        item_id: UUID,
        response: Response,
        db: AsyncSession = Depends(get_db),
        item_service: ItemDataService = Depends(get_item_service)
):
    """Get a single item by its id."""
    item = await item_service.get(db=db, id_=item_id)
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
async def update_item(
        item_id: UUID,
        item_update: ItemUpdate,
        response: Response,
        if_match: str = Header(...),    # return 422 if missing Header
        db: AsyncSession = Depends(get_db),
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
    updated_item = await item_service.update_with_lock(
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
async def delete_item(
        item_id: UUID,
        db: AsyncSession = Depends(get_db),
        item_service: ItemDataService = Depends(get_item_service)
):
    """Delete an item."""
    # Check if the row exists
    db_item = await item_service.get(db=db, id_=item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    await item_service.delete(db=db, id_=item_id)
    return