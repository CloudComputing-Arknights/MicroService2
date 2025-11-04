from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from typing import List, Optional

from framework.database import get_db
from services.ItemDataService import get_item_service, ItemDataService
from models.item import ItemCreate, ItemUpdate, ItemRead, CategoryType, TransactionType

router = APIRouter(
    prefix="/items",
    tags=["Items"]
)

@router.post("/", response_model=ItemRead, status_code=201)
def create_item(
        item_in: ItemCreate,
        db: Session = Depends(get_db),
        item_service: ItemDataService = Depends(get_item_service)
) -> ItemRead:
    """
    Create a new item record.
    """
    item = item_service.create(db=db, obj_in=item_in, user_UUID=item_in.user_UUID)
    return item


@router.get("/", response_model=List[ItemRead])
def list_items(
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
        category=category,
        transaction_type=transaction_type,
        skip=skip,
        limit=limit
    )
    return items


@router.get("/{item_id}", response_model=ItemRead)
def get_item(
        item_id: UUID,
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
    return item


@router.patch("/{item_id}", response_model=ItemRead)
def update_item(
        item_id: UUID,
        item_update: ItemUpdate,
        db: Session = Depends(get_db),
        item_service: ItemDataService = Depends(get_item_service)
):
    """Partially update an item's information."""
    # Check if the row exists
    db_item = item_service.get(db=db, id_=item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    # Check permissions
    # if db_item.user_UUID != current_user_id:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Not authorized to update this item"
    #     )

    updated_item = item_service.update(db=db, db_obj=db_item, obj_in=item_update)
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

    # Check permissions
    # if db_item.user_UUID != current_user_id:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Not authorized to delete this item"
    #     )
    item_service.delete(db=db, id_=item_id)
    return