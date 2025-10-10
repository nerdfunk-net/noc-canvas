"""
Inventory API router for managing device inventories.
"""

from __future__ import annotations
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..api.auth import get_current_user
from ..models.user import User
from ..schemas.inventory import (
    InventoryPreviewRequest,
    InventoryPreviewResponse,
    InventoryCreate,
    InventoryUpdate,
    InventoryResponse,
    InventoryListItem,
)
from ..services.inventory import inventory_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/preview", response_model=InventoryPreviewResponse)
async def preview_inventory(
    request: InventoryPreviewRequest,
    current_user: User = Depends(get_current_user),
) -> InventoryPreviewResponse:
    """
    Preview inventory by executing logical operations and returning matching devices.
    """
    try:
        logger.debug(
            f"Preview inventory request received from user: {current_user.username}"
        )
        logger.debug(f"Request operations: {request.operations}")

        if not request.operations:
            logger.debug("No operations provided, returning empty result")
            return InventoryPreviewResponse(
                devices=[], total_count=0, operations_executed=0
            )

        # Log each operation for debugging
        for i, operation in enumerate(request.operations):
            logger.debug(
                f"Operation {i}: type={operation.operation_type}, "
                f"conditions={len(operation.conditions)}, "
                f"nested={len(operation.nested_operations)}"
            )
            for j, condition in enumerate(operation.conditions):
                logger.debug(
                    f"  Condition {j}: field={condition.field}, "
                    f"operator={condition.operator}, value='{condition.value}'"
                )

        devices, operations_count = await inventory_service.preview_inventory(
            request.operations
        )

        logger.debug(
            f"Preview completed: {len(devices)} devices found, {operations_count} operations executed"
        )

        return InventoryPreviewResponse(
            devices=devices,
            total_count=len(devices),
            operations_executed=operations_count,
        )

    except Exception as e:
        logger.error(f"Error previewing inventory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to preview inventory: {str(e)}",
        )


@router.get("/inventories", response_model=List[InventoryListItem])
async def get_inventories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all inventories for the current user.
    """
    try:
        inventories = inventory_service.get_inventories(db, current_user)

        # Convert to list items (optionally add device_count later)
        result = []
        for inventory in inventories:
            result.append(
                InventoryListItem(
                    id=inventory.id,
                    name=inventory.name,
                    description=inventory.description,
                    owner_id=inventory.owner_id,
                    created_at=inventory.created_at,
                    updated_at=inventory.updated_at,
                    device_count=None,  # Could be calculated if needed
                )
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting inventories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get inventories: {str(e)}",
        )


@router.get("/inventories/{inventory_id}", response_model=InventoryResponse)
async def get_inventory(
    inventory_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a specific inventory by ID.
    """
    try:
        inventory = inventory_service.get_inventory(db, inventory_id, current_user)

        if not inventory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inventory with ID {inventory_id} not found",
            )

        # Parse operations from JSON
        operations = inventory_service.parse_operations_from_json(
            inventory.operations_json
        )

        return InventoryResponse(
            id=inventory.id,
            name=inventory.name,
            description=inventory.description,
            operations=operations,
            owner_id=inventory.owner_id,
            created_at=inventory.created_at,
            updated_at=inventory.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting inventory {inventory_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get inventory: {str(e)}",
        )


@router.post("/inventories", response_model=InventoryResponse)
async def create_inventory(
    request: InventoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new inventory.
    """
    try:
        inventory = inventory_service.create_inventory(
            db, request.name, request.description, request.operations, current_user
        )

        # Parse operations for response
        operations = inventory_service.parse_operations_from_json(
            inventory.operations_json
        )

        return InventoryResponse(
            id=inventory.id,
            name=inventory.name,
            description=inventory.description,
            operations=operations,
            owner_id=inventory.owner_id,
            created_at=inventory.created_at,
            updated_at=inventory.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating inventory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create inventory: {str(e)}",
        )


@router.put("/inventories/{inventory_id}", response_model=InventoryResponse)
async def update_inventory(
    inventory_id: int,
    request: InventoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update an existing inventory.
    """
    try:
        inventory = inventory_service.update_inventory(
            db,
            inventory_id,
            current_user,
            request.name,
            request.description,
            request.operations,
        )

        if not inventory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inventory with ID {inventory_id} not found",
            )

        # Parse operations for response
        operations = inventory_service.parse_operations_from_json(
            inventory.operations_json
        )

        return InventoryResponse(
            id=inventory.id,
            name=inventory.name,
            description=inventory.description,
            operations=operations,
            owner_id=inventory.owner_id,
            created_at=inventory.created_at,
            updated_at=inventory.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating inventory {inventory_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update inventory: {str(e)}",
        )


@router.delete("/inventories/{inventory_id}")
async def delete_inventory(
    inventory_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete an inventory.
    """
    try:
        success = inventory_service.delete_inventory(db, inventory_id, current_user)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inventory with ID {inventory_id} not found",
            )

        return {"message": "Inventory deleted successfully", "id": inventory_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting inventory {inventory_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete inventory: {str(e)}",
        )


@router.get("/field-options")
async def get_field_options(current_user: User = Depends(get_current_user)) -> dict:
    """
    Get available field options for building logical operations.
    """
    try:
        return {
            "fields": [
                {"value": "name", "label": "Device Name"},
                {"value": "location", "label": "Location"},
                {"value": "role", "label": "Role"},
                {"value": "tag", "label": "Tag"},
                {"value": "device_type", "label": "Device Type"},
                {"value": "manufacturer", "label": "Manufacturer"},
                {"value": "platform", "label": "Platform"},
                {"value": "custom_fields", "label": "Custom Fields..."},
            ],
            "operators": [
                {"value": "equals", "label": "Equals"},
                {"value": "contains", "label": "Contains"},
            ],
            "logical_operations": [
                {"value": "AND", "label": "AND"},
                {"value": "OR", "label": "OR"},
                {"value": "NOT", "label": "NOT"},
            ],
        }

    except Exception as e:
        logger.error(f"Error getting field options: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get field options: {str(e)}",
        )


@router.get("/custom-fields")
async def get_custom_fields(current_user: User = Depends(get_current_user)) -> dict:
    """
    Get available custom fields for building logical operations.
    """
    try:
        custom_fields = await inventory_service.get_custom_fields()
        return {"custom_fields": custom_fields}

    except Exception as e:
        logger.error(f"Error getting custom fields: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get custom fields: {str(e)}",
        )


@router.get("/field-values/{field_name}")
async def get_field_values(
    field_name: str, current_user: User = Depends(get_current_user)
) -> dict:
    """
    Get available values for a specific field for dropdown population.
    """
    try:
        field_values = await inventory_service.get_field_values(field_name)
        return {
            "field": field_name,
            "values": field_values,
            "input_type": "select" if field_values else "text",
        }

    except Exception as e:
        logger.error(f"Error getting field values for '{field_name}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get field values: {str(e)}",
        )
