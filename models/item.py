from typing import Optional, List, Annotated
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import Field, BaseModel
from decimal import Decimal
from enum import Enum


class TransactionType(str, Enum):
    SALE = "SALE"
    RENT = "RENT"


class ConditionType(str, Enum):
    BRAND_NEW = "BRAND_NEW"
    LIKE_NEW = "LIKE_NEW"
    GOOD = "GOOD"
    POOR = "POOR"


# =================================== Category ===================================
class CategoryBase(BaseModel):
    """Base model for a Category."""
    name: str = Field(
        ...,
        description="Name of the category",
        min_length=1,
        max_length=100
    )
    description: Optional[str] = Field(
        None,
        description="Optional description for the category."
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "FURNITURE",
                    "description": "Items for your home"
                }
            ]
        }
    }


class CategoryRead(CategoryBase):
    """Representation of a Category returned from the server."""
    category_id: int = Field(
        ...,
        description="Unique integer ID for the category"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "category_id": 1,
                    "name": "FURNITURE",
                    "description": "Items for your home"
                }
            ]
        }
    }

# =================================== Item ===================================
class ItemBase(BaseModel):
    title: str = Field(
        ...,
        description="Title of the post of the item"
    )
    description: Optional[str] = Field(
        default=None,
        description="Description of the item in the post."
    )
    condition: ConditionType = Field(
        ...,
        description="Condition of the item (ConditionType)"
    )
    transaction_type: TransactionType = Field(
        ...,
        description="Type of the transaction, can be SALE or RENT."
    )
    price: float = Annotated[
        Decimal,
        Field(
            ...,
            ge=0,
            max_digits=10,
            decimal_places=2,
            description="Price with <= 2 decimal places"
        )
    ]
    address_UUID: Optional[UUID] = Field(
        default_factory=list,
        description="The UUID of position for transaction chosen from user's address lists, can be online or a physical place, "
    )
    image_urls: List[str] = Field(
        default_factory=list,
        description="The list of URL images of the post"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Sofa",
                    "description": "Brown sofa.",
                    "condition": "LIKE_NEW",
                    "transaction_type": "SALE",
                    "price": 200.00,
                    "address_UUID": "99999999-9999-4999-8999-000000000001",
                    "image_urls": [
                        "https://example.com/image1.jpg",
                    ]
                }
            ]
        }
    }


class ItemCreate(ItemBase):
    """Creation payload for an item and its post."""
    category_ids: Optional[List[int]] = Field(
        default_factory=list,
        description="List of Category IDs to associate with this item."
    )
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Sofa",
                    "description": "Brown sofa.",
                    "condition": "LIKE_NEW",
                    "transaction_type": "SALE",
                    "price": 200.00,
                    "address_UUID": "99999999-9999-4999-8999-000000000001",
                    "image_urls": [
                        "https://example.com/image1.jpg",
                    ],
                    "category_ids": [
                        1,
                    ]
                }
            ]
        }
    }


class ItemUpdate(BaseModel):
    """Partial update for an item and its post."""
    title: Optional[str] = Field(
        None,
        description="Title of the post of the item"
    )
    description: Optional[str] = Field(
        None,
        description="Description of the item."
    )
    condition: Optional[ConditionType] = Field(
        None,
        description="Condition of the item (ConditionType)"
    )
    category_ids: Optional[List[int]] = Field(
        None,
        description="A new list of Category IDs to associate with this item. (Replaces the old list)"
    )
    transaction_type: Optional[TransactionType] = Field(
        None,
        description="Type of the transaction can be SALE or RENT."
    )
    price: float = Annotated[
        Decimal,
        Field(
            None,
            ge=0,
            max_digits=10,
            decimal_places=2,
            description="Price with <= 2 decimal places"
        )
    ]
    address_UUID: Optional[UUID] = Field(
        None,
        description="The position for transaction, can be online or a physical place."
    )
    image_urls: Optional[List[str]] = Field(
        None,
        description="The list of URL images of the post"
    )


class ItemRead(ItemBase):
    """Server representation returned to clients."""
    item_UUID: UUID = Field(
        ...,
        description="Server-generated item ID",
        json_schema_extra={"example": "99999999-9999-4999-8999-999999999999"},
    )
    categories: List[CategoryRead] = Field(
        default_factory=list,
        description="Categories associated with the item."
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Creation timestamp (UTC).",
        json_schema_extra={"example": "2025-02-20T11:22:33Z"},
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp (UTC).",
        json_schema_extra={"example": "2025-02-21T13:00:00Z"},
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "sofa",
                    "description": "Brown sofa",
                    "condition": "LIKE_NEW",
                    "transaction_type": "SALE",
                    "price": 200.00,
                    "address_UUID": "99999999-9999-4999-8999-000000000001",
                    "image_urls": [
                        "https://example.com/image1.jpg",
                    ],
                    "item_UUID": "99999999-9999-4999-8999-999999999999",
                    "created_at": "2025-02-20T11:22:33Z",
                    "updated_at": "2025-02-21T13:00:00Z",
                    "categories": [
                        {
                            "category_id": 1,
                            "name": "FURNITURE",
                            "description": "Items for your home"
                        }
                    ]
                }
            ]
        }
    }
