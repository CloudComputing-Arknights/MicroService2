from typing import Optional, List, Annotated
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import Field, BaseModel
from enum import Enum


class TransactionType(str, Enum):
    SALE = "SALE"
    RENT = "RENT"


class ConditionType(str, Enum):
    BRAND_NEW = "BRAND_NEW"
    LIKE_NEW = "LIKE_NEW"
    GOOD = "GOOD"
    POOR = "POOR"


class CategoryType(str, Enum):
    FURNITURE = "FURNITURE"


class ItemBase(BaseModel):
    title: str = Field(
        ...,
        description="Title of the post of the item"
    )
    description: Optional[str] = Field(
        None,
        description="Description of the item in the post."
    )
    condition: ConditionType = Field(
        ...,
        description="Condition of the item (ConditionType)"
    )
    category: Optional[List[CategoryType]] = Field(
        None,
        description="Category of the posted item."
    )
    transaction_type: TransactionType = Field(
        ...,
        description="Type of the transaction, can be SALE or RENT."
    )
    price: float = Field(
        ...,
        ge=0,
        description="Price of the item must be greater than 0."
    )
    address_UUID: Optional[UUID] = Field(
        None,
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
                    "category": [
                        "FURNITURE",
                    ],
                    "transaction_type": "SALE",
                    "price": 200.00,
                    "address_UUID": "99999999-9999-4999-8999-000000000001",
                    "image_urls": [
                        "http://example.com/image1.jpg",
                    ]
                }
            ]
        }
    }


class ItemCreate(ItemBase):
    """Creation payload for an item and its post."""
    user_UUID: Optional[UUID] = Field(
        None,
    )
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_UUID": "99999999-9999-4999-8999-999999999999",
                    "title": "Sofa",
                    "description": "Brown sofa.",
                    "condition": "LIKE_NEW",
                    "category": [
                        "FURNITURE",
                    ],
                    "transaction_type": "SALE",
                    "price": 200.00,
                    "address_UUID": "99999999-9999-4999-8999-000000000001",
                    "image_urls": [
                        "http://example.com/image1.jpg",
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
    category: Optional[List[CategoryType]] = Field(
        None,
        description="Category of the posted item."
    )
    transaction_type: Optional[TransactionType] = Field(
        None,
        description="Type of the transaction can be SALE or RENT."
    )
    price: Optional[float] = Field(
        None,
        ge=0,
        description="Price of the item must be greater than 0."
    )
    address_UUID: Optional[UUID] = Field(
        None,
        description="The position for transaction, can be online or a physical place."
    )
    image_urls: Optional[List[str]] = Field(
        default_factory=list,
        description="The list of URL images of the post"
    )


class ItemRead(ItemBase):
    """Server representation returned to clients."""
    item_UUID: UUID = Field(
        ...,
        description="Server-generated item ID",
        json_schema_extra={"example": "99999999-9999-4999-8999-999999999999"},
    )
    user_UUID: UUID = Field(
        ...,
        description="Server-generated user ID",
        json_schema_extra={"example": "99999999-9999-4999-8999-999999999999"},
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
                    "category": [
                        "FURNITURE",
                    ],
                    "transaction_type": "SALE",
                    "price": 200.00,
                    "address_UUID": "99999999-9999-4999-8999-000000000001",
                    "image_urls": [
                        "http://example.com/image1.jpg",
                    ],
                    "item_UUID": "99999999-9999-4999-8999-999999999999",
                    "user_UUID": "99999999-9999-4999-8999-999999999998",
                    "created_at": "2025-02-20T11:22:33Z",
                    "updated_at": "2025-02-21T13:00:00Z",
                }
            ]
        }
    }
