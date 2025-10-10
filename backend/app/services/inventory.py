"""
Inventory service for managing device inventories and executing logical operations.
"""

from __future__ import annotations
import logging
import json
from typing import List, Dict, Any, Set, Optional
from sqlalchemy.orm import Session
from ..schemas.inventory import LogicalOperation, LogicalCondition, DeviceInfo
from ..models.inventory import Inventory
from ..models.user import User

logger = logging.getLogger(__name__)


class InventoryService:
    """Service for handling inventory operations."""

    def __init__(self):
        """Initialize the service."""
        # Map field names to GraphQL query functions
        self.field_to_query_map = {
            "name": self._query_devices_by_name,
            "location": self._query_devices_by_location,
            "role": self._query_devices_by_role,
            "tag": self._query_devices_by_tag,
            "device_type": self._query_devices_by_devicetype,
            "manufacturer": self._query_devices_by_manufacturer,
            "platform": self._query_devices_by_platform,
        }
        # Cache for custom fields to avoid repeated API calls
        self._custom_fields_cache = None

    # ========== CRUD Operations ==========

    def get_inventories(self, db: Session, user: User) -> List[Inventory]:
        """Get all inventories for a user."""
        return db.query(Inventory).filter(Inventory.owner_id == user.id).all()

    def get_inventory(
        self, db: Session, inventory_id: int, user: User
    ) -> Optional[Inventory]:
        """Get a specific inventory by ID."""
        return (
            db.query(Inventory)
            .filter(Inventory.id == inventory_id, Inventory.owner_id == user.id)
            .first()
        )

    def create_inventory(
        self,
        db: Session,
        name: str,
        description: Optional[str],
        operations: List[LogicalOperation],
        user: User,
    ) -> Inventory:
        """Create a new inventory."""
        operations_json = json.dumps([op.model_dump() for op in operations])

        inventory = Inventory(
            name=name,
            description=description,
            operations_json=operations_json,
            owner_id=user.id,
        )

        db.add(inventory)
        db.commit()
        db.refresh(inventory)
        return inventory

    def update_inventory(
        self,
        db: Session,
        inventory_id: int,
        user: User,
        name: Optional[str] = None,
        description: Optional[str] = None,
        operations: Optional[List[LogicalOperation]] = None,
    ) -> Optional[Inventory]:
        """Update an existing inventory."""
        inventory = self.get_inventory(db, inventory_id, user)
        if not inventory:
            return None

        if name is not None:
            inventory.name = name
        if description is not None:
            inventory.description = description
        if operations is not None:
            inventory.operations_json = json.dumps(
                [op.model_dump() for op in operations]
            )

        db.commit()
        db.refresh(inventory)
        return inventory

    def delete_inventory(self, db: Session, inventory_id: int, user: User) -> bool:
        """Delete an inventory."""
        inventory = self.get_inventory(db, inventory_id, user)
        if not inventory:
            return False

        db.delete(inventory)
        db.commit()
        return True

    def parse_operations_from_json(
        self, operations_json: str
    ) -> List[LogicalOperation]:
        """Parse operations from JSON string."""
        try:
            operations_data = json.loads(operations_json)
            return [LogicalOperation(**op) for op in operations_data]
        except Exception as e:
            logger.error(f"Error parsing operations JSON: {e}")
            return []

    # ========== Device Query Operations ==========

    async def preview_inventory(
        self, operations: List[LogicalOperation]
    ) -> tuple[List[DeviceInfo], int]:
        """
        Preview inventory by executing logical operations and returning matching devices.

        Args:
            operations: List of logical operations to execute

        Returns:
            Tuple of (devices, operations_count)
        """
        try:
            logger.info(f"Preview inventory called with {len(operations)} operations")

            # Start with empty result set
            result_devices: Set[str] = set()  # Use device IDs for set operations
            all_devices_data: Dict[str, DeviceInfo] = {}
            operations_count = 0

            # Process each top-level operation
            for i, operation in enumerate(operations):
                logger.info(
                    f"Processing operation {i}: type={operation.operation_type}, "
                    f"conditions={len(operation.conditions)}, nested={len(operation.nested_operations)}"
                )

                (
                    operation_result,
                    op_count,
                    devices_data,
                ) = await self._execute_operation(operation)
                operations_count += op_count
                all_devices_data.update(devices_data)

                logger.info(
                    f"Operation {i} result: {len(operation_result)} devices, {op_count} queries"
                )

                # Apply the operation result to our main result set
                if not result_devices:  # First operation
                    if operation.operation_type.upper() == "NOT":
                        # NOT operation as first operation means start with empty set
                        result_devices = set()
                        logger.info("First operation is NOT, starting with empty set")
                    else:
                        result_devices = operation_result
                        logger.info(
                            f"First operation set result devices to {len(result_devices)} devices"
                        )
                else:
                    # Handle different operation types
                    if operation.operation_type.upper() == "NOT":
                        # Subtract the NOT operation result from current result
                        old_count = len(result_devices)
                        result_devices = result_devices.difference(operation_result)
                        logger.info(
                            f"Applied NOT: {old_count} - {len(operation_result)} = {len(result_devices)} devices"
                        )
                    else:
                        # For AND/OR operations, combine with intersection (AND behavior)
                        old_count = len(result_devices)
                        result_devices = result_devices.intersection(operation_result)
                        logger.info(
                            f"Combined with AND: {old_count} ∩ {len(operation_result)} = {len(result_devices)} devices"
                        )

            # Convert result to list of DeviceInfo objects
            result_list = [
                all_devices_data[device_id]
                for device_id in result_devices
                if device_id in all_devices_data
            ]

            logger.info(
                f"Preview completed: {len(result_list)} devices found, {operations_count} operations executed"
            )

            return result_list, operations_count

        except Exception as e:
            logger.error(f"Error previewing inventory: {e}")
            raise

    async def _execute_operation(
        self, operation: LogicalOperation
    ) -> tuple[Set[str], int, Dict[str, DeviceInfo]]:
        """
        Execute a single logical operation.

        Args:
            operation: The logical operation to execute

        Returns:
            Tuple of (device_ids_set, operations_count, devices_data)
        """
        logger.info(
            f"Executing operation: type={operation.operation_type}, "
            f"conditions={len(operation.conditions)}, nested={len(operation.nested_operations)}"
        )

        operations_count = 0
        all_devices_data: Dict[str, DeviceInfo] = {}

        # Execute all conditions in this operation
        condition_results: List[Set[str]] = []

        for i, condition in enumerate(operation.conditions):
            logger.info(
                f"  Executing condition {i}: {condition.field} {condition.operator} '{condition.value}'"
            )
            devices, op_count, devices_data = await self._execute_condition(condition)
            condition_results.append(devices)
            operations_count += op_count
            all_devices_data.update(devices_data)
            logger.info(f"  Condition {i} result: {len(devices)} devices")

        # Execute nested operations
        for i, nested_op in enumerate(operation.nested_operations):
            logger.info(f"  Executing nested operation {i}")
            nested_result, nested_count, nested_data = await self._execute_operation(
                nested_op
            )
            condition_results.append(nested_result)
            operations_count += nested_count
            all_devices_data.update(nested_data)
            logger.info(f"  Nested operation {i} result: {len(nested_result)} devices")

        # Combine results based on operation type
        if operation.operation_type.upper() == "AND":
            result = self._intersect_sets(condition_results)
            logger.info(f"  AND operation result: {len(result)} devices")
        elif operation.operation_type.upper() == "OR":
            result = self._union_sets(condition_results)
            logger.info(f"  OR operation result: {len(result)} devices")
        elif operation.operation_type.upper() == "NOT":
            # For NOT operations, return the devices that match the conditions
            if condition_results:
                result = self._union_sets(condition_results)
            else:
                result = set()
            logger.info(f"  NOT operation devices to exclude: {len(result)} devices")
        else:
            logger.warning(f"Unknown operation type: {operation.operation_type}")
            result = set()

        logger.info(
            f"Operation completed: {len(result)} devices, {operations_count} total queries"
        )
        return result, operations_count, all_devices_data

    async def _execute_condition(
        self, condition: LogicalCondition
    ) -> tuple[Set[str], int, Dict[str, DeviceInfo]]:
        """
        Execute a single condition by calling the appropriate GraphQL query.

        Args:
            condition: The condition to execute

        Returns:
            Tuple of (device_ids_set, operations_count, devices_data)
        """
        try:
            # Check if this is a custom field (starts with cf_)
            if condition.field.startswith("cf_"):
                use_contains = condition.operator == "contains"
                devices_data = await self._query_devices_by_custom_field(
                    condition.field, condition.value, use_contains
                )
                device_ids = {device.id for device in devices_data}
                devices_dict = {device.id: device for device in devices_data}
                return device_ids, 1, devices_dict

            # Handle regular fields
            query_func = self.field_to_query_map.get(condition.field)
            if not query_func:
                logger.error(f"No query function found for field: {condition.field}")
                return set(), 0, {}

            # Determine if we should use contains matching
            use_contains = condition.operator == "contains"

            # Only name and location support contains matching
            if condition.field in ["name", "location"] and use_contains:
                devices_data = await query_func(condition.value, use_contains=True)
            elif condition.field in ["name", "location"]:
                devices_data = await query_func(condition.value, use_contains=False)
            else:
                # Other fields only support exact matching
                if use_contains:
                    logger.warning(
                        f"Field {condition.field} does not support 'contains' operator, using exact match"
                    )
                devices_data = await query_func(condition.value)

            device_ids = {device.id for device in devices_data}
            devices_dict = {device.id: device for device in devices_data}

            logger.info(
                f"Condition {condition.field} {condition.operator} '{condition.value}' returned {len(devices_data)} devices"
            )

            return device_ids, 1, devices_dict

        except Exception as e:
            logger.error(
                f"Error executing condition {condition.field}={condition.value}: {e}"
            )
            return set(), 0, {}

    def _intersect_sets(self, sets: List[Set[str]]) -> Set[str]:
        """Compute intersection of multiple sets (AND operation)."""
        if not sets:
            return set()
        result = sets[0]
        for s in sets[1:]:
            result = result.intersection(s)
        return result

    def _union_sets(self, sets: List[Set[str]]) -> Set[str]:
        """Compute union of multiple sets (OR operation)."""
        result = set()
        for s in sets:
            result = result.union(s)
        return result

    # ========== GraphQL Query Methods ==========

    async def _query_devices_by_name(
        self, name_filter: str, use_contains: bool = False
    ) -> List[DeviceInfo]:
        """Query devices by name using GraphQL."""
        from ..services.nautobot import nautobot_service

        # Use different queries based on match type
        if use_contains:
            query = """
            query devices_by_name($name_filter: [String]) {
                devices(name__ic: $name_filter) {
                    id
                    name
                    primary_ip4 {
                        address
                    }
                    status {
                        name
                    }
                    device_type {
                        model
                    }
                    role {
                        name
                    }
                    location {
                        name
                    }
                    tags {
                        name
                    }
                    platform {
                        name
                    }
                }
            }
            """
        else:
            query = """
            query devices_by_name($name_filter: [String]) {
                devices(name: $name_filter) {
                    id
                    name
                    primary_ip4 {
                        address
                    }
                    status {
                        name
                    }
                    device_type {
                        model
                    }
                    role {
                        name
                    }
                    location {
                        name
                    }
                    tags {
                        name
                    }
                    platform {
                        name
                    }
                }
            }
            """

        variables = {"name_filter": [name_filter]}
        result = await nautobot_service.graphql_query(query, variables)
        devices_data = result.get("data", {}).get("devices", [])
        return self._parse_device_data(devices_data)

    async def _query_devices_by_location(
        self, location_filter: str, use_contains: bool = False
    ) -> List[DeviceInfo]:
        """Query devices by location using GraphQL."""
        from ..services.nautobot import nautobot_service

        if use_contains:
            query = """
            query devices_by_location($location_filter: [String]) {
                locations(name__ic: $location_filter) {
                    devices {
                        id
                        name
                        primary_ip4 {
                            address
                        }
                        status {
                            name
                        }
                        device_type {
                            model
                        }
                        role {
                            name
                        }
                        location {
                            name
                        }
                        tags {
                            name
                        }
                        platform {
                            name
                        }
                    }
                }
            }
            """
        else:
            query = """
            query devices_by_location($location_filter: [String]) {
                locations(name: $location_filter) {
                    devices {
                        id
                        name
                        primary_ip4 {
                            address
                        }
                        status {
                            name
                        }
                        device_type {
                            model
                        }
                        role {
                            name
                        }
                        location {
                            name
                        }
                        tags {
                            name
                        }
                        platform {
                            name
                        }
                    }
                }
            }
            """

        variables = {"location_filter": [location_filter]}
        result = await nautobot_service.graphql_query(query, variables)

        devices = []
        for location in result.get("data", {}).get("locations", []):
            devices.extend(location.get("devices", []))

        return self._parse_device_data(devices)

    async def _query_devices_by_role(self, role_filter: str) -> List[DeviceInfo]:
        """Query devices by role using GraphQL."""
        from ..services.nautobot import nautobot_service

        query = """
        query devices_by_role($role_filter: [String]) {
            devices(role: $role_filter) {
                id
                name
                primary_ip4 {
                    address
                }
                status {
                    name
                }
                device_type {
                    model
                }
                role {
                    name
                }
                location {
                    name
                }
                tags {
                    name
                }
                platform {
                    name
                }
            }
        }
        """

        variables = {"role_filter": [role_filter]}
        result = await nautobot_service.graphql_query(query, variables)
        return self._parse_device_data(result.get("data", {}).get("devices", []))

    async def _query_devices_by_tag(self, tag_filter: str) -> List[DeviceInfo]:
        """Query devices by tag using GraphQL."""
        from ..services.nautobot import nautobot_service

        query = """
        query devices_by_tag($tag_filter: [String]) {
            devices(tags: $tag_filter) {
                id
                name
                primary_ip4 {
                    address
                }
                status {
                    name
                }
                device_type {
                    model
                }
                role {
                    name
                }
                location {
                    name
                }
                tags {
                    name
                }
                platform {
                    name
                }
            }
        }
        """

        variables = {"tag_filter": [tag_filter]}
        result = await nautobot_service.graphql_query(query, variables)
        return self._parse_device_data(result.get("data", {}).get("devices", []))

    async def _query_devices_by_devicetype(
        self, devicetype_filter: str
    ) -> List[DeviceInfo]:
        """Query devices by device type using GraphQL."""
        from ..services.nautobot import nautobot_service

        query = """
        query devices_by_devicetype($devicetype_filter: [String]) {
            devices(device_type: $devicetype_filter) {
                id
                name
                primary_ip4 {
                    address
                }
                status {
                    name
                }
                device_type {
                    model
                }
                role {
                    name
                }
                location {
                    name
                }
                tags {
                    name
                }
                platform {
                    name
                }
            }
        }
        """

        variables = {"devicetype_filter": [devicetype_filter]}
        result = await nautobot_service.graphql_query(query, variables)
        return self._parse_device_data(result.get("data", {}).get("devices", []))

    async def _query_devices_by_manufacturer(
        self, manufacturer_filter: str
    ) -> List[DeviceInfo]:
        """Query devices by manufacturer using GraphQL."""
        from ..services.nautobot import nautobot_service

        query = """
        query devices_by_manufacturer($manufacturer_filter: [String]) {
            devices(manufacturer: $manufacturer_filter) {
                id
                name
                primary_ip4 {
                    address
                }
                status {
                    name
                }
                device_type {
                    model
                }
                role {
                    name
                }
                location {
                    name
                }
                tags {
                    name
                }
                platform {
                    name
                }
            }
        }
        """

        variables = {"manufacturer_filter": [manufacturer_filter]}
        result = await nautobot_service.graphql_query(query, variables)
        return self._parse_device_data(result.get("data", {}).get("devices", []))

    async def _query_devices_by_platform(
        self, platform_filter: str
    ) -> List[DeviceInfo]:
        """Query devices by platform using GraphQL."""
        from ..services.nautobot import nautobot_service

        query = """
        query devices_by_platform($platform_filter: [String]) {
            devices(platform: $platform_filter) {
                id
                name
                primary_ip4 {
                    address
                }
                status {
                    name
                }
                device_type {
                    model
                }
                role {
                    name
                }
                location {
                    name
                }
                tags {
                    name
                }
                platform {
                    name
                }
            }
        }
        """

        variables = {"platform_filter": [platform_filter]}
        result = await nautobot_service.graphql_query(query, variables)
        return self._parse_device_data(result.get("data", {}).get("devices", []))

    async def _query_devices_by_custom_field(
        self,
        custom_field_name: str,
        custom_field_value: str,
        use_contains: bool = False,
    ) -> List[DeviceInfo]:
        """Query devices by custom field value."""
        from ..services.nautobot import nautobot_service

        try:
            # Build the GraphQL query with custom field filter
            if use_contains:
                filter_str = f"{custom_field_name}__ic"
            else:
                filter_str = custom_field_name

            query = f"""
            query devices_by_custom_field($field_value: [String]) {{
                devices({filter_str}: $field_value) {{
                    id
                    name
                    primary_ip4 {{
                        address
                    }}
                    status {{
                        name
                    }}
                    device_type {{
                        model
                    }}
                    role {{
                        name
                    }}
                    location {{
                        name
                    }}
                    tags {{
                        name
                    }}
                    platform {{
                        name
                    }}
                }}
            }}
            """

            variables = {"field_value": [custom_field_value]}
            result = await nautobot_service.graphql_query(query, variables)
            return self._parse_device_data(result.get("data", {}).get("devices", []))

        except Exception as e:
            logger.error(f"Error querying custom field {custom_field_name}: {e}")
            return []

    def _parse_device_data(
        self, devices_data: List[Dict[str, Any]]
    ) -> List[DeviceInfo]:
        """Parse GraphQL device data into DeviceInfo objects."""
        devices = []

        for device_data in devices_data:
            try:
                device_info = DeviceInfo(
                    id=device_data.get("id", ""),
                    name=device_data.get("name", ""),
                    location=device_data.get("location", {}).get("name")
                    if device_data.get("location")
                    else None,
                    role=device_data.get("role", {}).get("name")
                    if device_data.get("role")
                    else None,
                    device_type=device_data.get("device_type", {}).get("model")
                    if device_data.get("device_type")
                    else None,
                    manufacturer=None,  # Not in standard query
                    platform=device_data.get("platform", {}).get("name")
                    if device_data.get("platform")
                    else None,
                    primary_ip4=device_data.get("primary_ip4", {}).get("address")
                    if device_data.get("primary_ip4")
                    else None,
                    status=device_data.get("status", {}).get("name")
                    if device_data.get("status")
                    else None,
                    tags=[tag.get("name", "") for tag in device_data.get("tags", [])]
                    if device_data.get("tags")
                    else [],
                )
                devices.append(device_info)
            except Exception as e:
                logger.error(f"Error parsing device data: {e}")
                continue

        return devices

    # ========== Helper Methods for UI ==========

    async def get_custom_fields(self) -> List[Dict[str, Any]]:
        """Get available custom fields for devices."""
        from ..services.nautobot import nautobot_service

        try:
            query = """
            query {
                custom_fields(content_types: "dcim.device") {
                    name
                    label
                    type
                }
            }
            """

            result = await nautobot_service.graphql_query(query, {})
            custom_fields = result.get("data", {}).get("custom_fields", [])

            return [
                {
                    "name": f"cf_{field['name']}",
                    "label": field.get("label", field["name"]),
                    "type": field.get("type", "text"),
                }
                for field in custom_fields
            ]

        except Exception as e:
            logger.error(f"Error fetching custom fields: {e}")
            return []

    async def get_field_values(self, field_name: str) -> List[Dict[str, str]]:
        """Get available values for a specific field."""
        from ..services.nautobot import nautobot_service

        try:
            # Map field names to GraphQL queries
            if field_name == "location":
                query = """
                query {
                    locations {
                        id
                        name
                        parent { id }
                    }
                }
                """
                result = await nautobot_service.graphql_query(query, {})
                locations = result.get("data", {}).get("locations", [])

                # Build hierarchical paths
                location_map = {loc["id"]: loc for loc in locations}
                for location in locations:
                    path = []
                    current = location
                    while current:
                        path.insert(0, current["name"])
                        parent_id = (
                            current.get("parent", {}).get("id")
                            if current.get("parent")
                            else None
                        )
                        current = location_map.get(parent_id) if parent_id else None
                    location["hierarchicalPath"] = " → ".join(path)

                # Sort by hierarchical path
                locations.sort(key=lambda x: x.get("hierarchicalPath", ""))

                return [
                    {
                        "value": loc["name"],
                        "label": loc.get("hierarchicalPath", loc["name"]),
                    }
                    for loc in locations
                ]

            elif field_name == "role":
                query = """
                query {
                    roles {
                        name
                    }
                }
                """
                result = await nautobot_service.graphql_query(query, {})
                roles = result.get("data", {}).get("roles", [])
                return [
                    {"value": role["name"], "label": role["name"]} for role in roles
                ]

            elif field_name == "tag":
                query = """
                query {
                    tags {
                        name
                    }
                }
                """
                result = await nautobot_service.graphql_query(query, {})
                tags = result.get("data", {}).get("tags", [])
                return [{"value": tag["name"], "label": tag["name"]} for tag in tags]

            elif field_name == "device_type":
                query = """
                query {
                    device_types {
                        model
                    }
                }
                """
                result = await nautobot_service.graphql_query(query, {})
                device_types = result.get("data", {}).get("device_types", [])
                return [
                    {"value": dt["model"], "label": dt["model"]} for dt in device_types
                ]

            elif field_name == "manufacturer":
                query = """
                query {
                    manufacturers {
                        name
                    }
                }
                """
                result = await nautobot_service.graphql_query(query, {})
                manufacturers = result.get("data", {}).get("manufacturers", [])
                return [
                    {"value": mfr["name"], "label": mfr["name"]}
                    for mfr in manufacturers
                ]

            elif field_name == "platform":
                query = """
                query {
                    platforms {
                        name
                    }
                }
                """
                result = await nautobot_service.graphql_query(query, {})
                platforms = result.get("data", {}).get("platforms", [])
                return [
                    {"value": plat["name"], "label": plat["name"]} for plat in platforms
                ]

            else:
                return []

        except Exception as e:
            logger.error(f"Error fetching field values for {field_name}: {e}")
            return []


# Global service instance
inventory_service = InventoryService()
