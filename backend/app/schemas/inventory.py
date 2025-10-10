"""
Pydantic schemas for inventory management.
"""

from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class LogicalCondition(BaseModel):
    """Represents a single logical condition for device filtering."""

    field: str = Field(..., description="Device field to filter on")
    operator: str = Field(..., description="Logical operator (equals, contains, etc.)")
    value: str = Field(..., description="Value to filter by")


class LogicalOperation(BaseModel):
    """Represents a logical operation with conditions."""

    operation_type: str = Field(..., description="Type of operation: AND, OR, NOT")
    conditions: List[LogicalCondition] = Field(default_factory=list)
    nested_operations: List["LogicalOperation"] = Field(default_factory=list)


# Update forward references
LogicalOperation.model_rebuild()


class DeviceInfo(BaseModel):
    """Device information for inventory."""

    id: str = Field(..., description="Device UUID")
    name: str = Field(..., description="Device name")
    location: Optional[str] = Field(None, description="Device location")
    role: Optional[str] = Field(None, description="Device role")
    tags: List[str] = Field(default_factory=list, description="Device tags")
    device_type: Optional[str] = Field(None, description="Device type")
    manufacturer: Optional[str] = Field(None, description="Device manufacturer")
    platform: Optional[str] = Field(None, description="Device platform")
    primary_ip4: Optional[str] = Field(None, description="Primary IPv4 address")
    status: Optional[str] = Field(None, description="Device status")


class InventoryPreviewRequest(BaseModel):
    """Request for previewing inventory based on logical operations."""

    operations: List[LogicalOperation] = Field(
        ..., description="List of logical operations"
    )


class InventoryPreviewResponse(BaseModel):
    """Response for inventory preview."""

    devices: List[DeviceInfo] = Field(
        ..., description="List of devices matching criteria"
    )
    total_count: int = Field(..., description="Total number of devices")
    operations_executed: int = Field(
        ..., description="Number of GraphQL operations executed"
    )


class InventoryCreate(BaseModel):
    """Request for creating a new inventory."""

    name: str = Field(..., description="Name of the inventory")
    description: Optional[str] = Field(None, description="Description of the inventory")
    operations: List[LogicalOperation] = Field(
        ..., description="List of logical operations"
    )


class InventoryUpdate(BaseModel):
    """Request for updating an inventory."""

    name: Optional[str] = Field(None, description="Name of the inventory")
    description: Optional[str] = Field(None, description="Description of the inventory")
    operations: Optional[List[LogicalOperation]] = Field(
        None, description="List of logical operations"
    )


class InventoryResponse(BaseModel):
    """Response for inventory operations."""

    id: int = Field(..., description="Inventory ID")
    name: str = Field(..., description="Name of the inventory")
    description: Optional[str] = Field(None, description="Description of the inventory")
    operations: List[LogicalOperation] = Field(
        ..., description="List of logical operations"
    )
    owner_id: int = Field(..., description="Owner user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class InventoryListItem(BaseModel):
    """Simplified inventory list item."""

    id: int = Field(..., description="Inventory ID")
    name: str = Field(..., description="Name of the inventory")
    description: Optional[str] = Field(None, description="Description of the inventory")
    owner_id: int = Field(..., description="Owner user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    device_count: Optional[int] = Field(None, description="Cached device count")

    class Config:
        from_attributes = True
