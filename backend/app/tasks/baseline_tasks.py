"""
Baseline tasks for capturing device configuration snapshots.

This module contains Celery tasks for creating and updating baseline configurations
for network devices. Baselines are used for configuration drift detection, compliance
checking, and change management.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from sqlalchemy import and_

logger = logging.getLogger(__name__)


def register_tasks(celery_app):
    """Register baseline tasks with the Celery app."""

    def _execute_snapshot_task(
        task_self,
        device_ids: Optional[List[str]] = None,
        inventory_id: Optional[int] = None,
        commands: Optional[List[str]] = None,
        notes: Optional[str] = None,
        auth_token: str = "",
        username: Optional[str] = None,
        snapshot_type: str = "baseline",
    ):
        """
        Create or update snapshots/baselines for devices.

        This task executes snapshot commands on devices and stores the output as
        snapshot or baseline data for future comparison. Commands are loaded from the
        device_commands table based on:
        - Command type = "snapshot"
        - Device platform (IOS, IOS XE, Nexus, etc.)

        The platform is determined from the device's Nautobot configuration and matched
        to the appropriate CommandPlatform enum. Only snapshot commands matching the
        device's platform are executed.

        Snapshot Types:
        - "baseline": Long-term reference snapshot, typically taken once and stored for comparison
        - "snapshot": Current state snapshot, typically used for comparison against baseline

        Args:
            device_ids: List of device IDs to baseline. If None, baselines all devices.
            inventory_id: ID of inventory to use for device selection. Takes precedence over device_ids.
            commands: List of specific commands to execute. If None, loads snapshot commands from database per device platform.
            notes: Optional notes to store with snapshot (e.g., "Pre-upgrade baseline")
            auth_token: Authentication token for device access (deprecated, use username instead)
            username: Username to use for credential lookup. If not provided, extracts from auth_token or defaults to 'admin'
            snapshot_type: Type of snapshot to create - "baseline" or "snapshot" (default: "baseline")

        Returns:
            Dictionary with snapshot creation results:
                - status: "completed" or "failed"
                - devices_processed: Number of devices successfully processed
                - total_devices: Total number of devices attempted
                - total_commands: Total commands executed
                - errors: List of errors encountered
                - snapshot_ids: List of created snapshot record IDs
        """
        from ..core.database import SessionLocal
        from ..models.device_cache import Snapshot, SnapshotType
        from ..models.inventory import Inventory
        from ..models.settings import DeviceCommand, CommandType, CommandPlatform
        from ..services.nautobot import nautobot_service
        from ..services.device_communication import DeviceCommunicationService
        from ..services.inventory import InventoryService
        from ..services.task_security import validate_task_username
        from ..schemas.inventory import LogicalOperation

        # Validate and convert snapshot_type parameter
        if snapshot_type.lower() == "baseline":
            snapshot_type_enum = SnapshotType.BASELINE
        elif snapshot_type.lower() == "snapshot":
            snapshot_type_enum = SnapshotType.SNAPSHOT
        else:
            raise ValueError(f"Invalid snapshot_type: {snapshot_type}. Must be 'baseline' or 'snapshot'")

        logger.info(f"Starting snapshot creation task (type: {snapshot_type})")

        try:
            task_self.update_state(
                state="PROGRESS",
                meta={"current": 0, "total": 100, "status": "Initializing"},
            )

            # Get username - priority: explicit username parameter > extract from token > default to 'admin'
            if username:
                task_username = username
            else:
                task_username = _get_username_from_token(auth_token)

            # Initialize database session
            db = SessionLocal()

            try:
                # Security validation: Verify username matches task owner
                # Get periodic_task_id from Celery request context if available
                periodic_task_id = None
                try:
                    # Celery provides request context with task metadata
                    if hasattr(task_self, "request") and hasattr(task_self.request, "properties"):
                        # Try to extract periodic task ID from task properties/headers
                        # This is set by celery-beat when running scheduled tasks
                        periodic_task_id = task_self.request.properties.get(
                            "periodic_task_name"
                        )
                        if periodic_task_id:
                            # Extract numeric ID if it's in format "celery.backend_cleanup_123"
                            import re

                            match = re.search(r"_(\d+)$", str(periodic_task_id))
                            if match:
                                periodic_task_id = int(match.group(1))
                            else:
                                periodic_task_id = None
                except Exception as e:
                    logger.debug(f"Could not extract periodic_task_id: {e}")

                # Validate and get the correct username to use
                is_valid, validated_username = validate_task_username(
                    db, periodic_task_id, task_username
                )

                if not is_valid:
                    logger.warning(
                        f"Username mismatch detected! Using validated username: {validated_username}"
                    )

                task_username = validated_username
                logger.info(
                    f"Running baseline task for validated user: {task_username}"
                )

                # Get devices to baseline
                # Priority: inventory_id > device_ids > all devices
                if inventory_id:
                    # Resolve inventory to device IDs
                    task_self.update_state(
                        state="PROGRESS",
                        meta={
                            "current": 3,
                            "total": 100,
                            "status": f"Resolving inventory {inventory_id} to devices",
                        },
                    )

                    inventory = (
                        db.query(Inventory).filter(Inventory.id == inventory_id).first()
                    )
                    if not inventory:
                        raise ValueError(f"Inventory {inventory_id} not found")

                    # Parse operations from JSON
                    operations_data = json.loads(inventory.operations_json)
                    operations = [LogicalOperation(**op) for op in operations_data]

                    # Use inventory service to preview devices
                    inventory_service = InventoryService()
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        devices_list, ops_count = loop.run_until_complete(
                            inventory_service.preview_inventory(operations)
                        )
                        device_ids = [d.id for d in devices_list]
                        logger.info(
                            f"Resolved inventory '{inventory.name}' to {len(device_ids)} devices"
                        )
                    finally:
                        loop.close()

                    if not device_ids:
                        logger.warning(
                            f"Inventory '{inventory.name}' resolved to zero devices"
                        )
                        return {
                            "status": "completed",
                            "devices_processed": 0,
                            "total_devices": 0,
                            "total_commands": 0,
                            "baseline_ids": [],
                            "errors": [],
                            "message": f"Inventory '{inventory.name}' contains no devices",
                        }

                if not device_ids:
                    # Get all devices from Nautobot if none specified
                    task_self.update_state(
                        state="PROGRESS",
                        meta={
                            "current": 5,
                            "total": 100,
                            "status": "Fetching devices from Nautobot",
                        },
                    )

                    # Run async function in event loop
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        devices_result = loop.run_until_complete(
                            nautobot_service.get_devices_async(
                                task_username, limit=1000
                            )
                        )
                        device_ids = [
                            d["id"] for d in devices_result.get("devices", [])
                        ]
                    finally:
                        loop.close()

                total_devices = len(device_ids)
                logger.info(f"Baselining {total_devices} devices")

                devices_processed = 0
                total_commands_executed = 0
                errors = []
                baseline_ids = []

                # Process each device
                for device_index, device_id in enumerate(device_ids):
                    try:
                        # Update progress
                        progress = 10 + int((device_index / total_devices) * 80)
                        task_self.update_state(
                            state="PROGRESS",
                            meta={
                                "current": progress,
                                "total": 100,
                                "status": f"Processing device {device_index + 1}/{total_devices}",
                                "devices_processed": devices_processed,
                                "total_commands_executed": total_commands_executed,
                            },
                        )

                        # Get device info from Nautobot
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            device_data = loop.run_until_complete(
                                nautobot_service.get_device(device_id, task_username)
                            )
                        finally:
                            loop.close()

                        if not device_data:
                            error_msg = f"Device {device_id} not found in Nautobot"
                            logger.warning(error_msg)
                            errors.append({"device_id": device_id, "error": error_msg})
                            continue

                        device_name = device_data.get("name", device_id)

                        # Validate device has required info
                        primary_ip4 = device_data.get("primary_ip4")
                        if not primary_ip4 or not primary_ip4.get("address"):
                            error_msg = f"Device {device_name} does not have a primary IPv4 address"
                            logger.warning(error_msg)
                            errors.append(
                                {
                                    "device_id": device_id,
                                    "device_name": device_name,
                                    "error": error_msg,
                                }
                            )
                            continue

                        platform_info = device_data.get("platform")
                        if not platform_info or not platform_info.get("network_driver"):
                            error_msg = f"Device {device_name} does not have platform/network_driver configured"
                            logger.warning(error_msg)
                            errors.append(
                                {
                                    "device_id": device_id,
                                    "device_name": device_name,
                                    "error": error_msg,
                                }
                            )
                            continue

                        # Prepare device info for command execution
                        device_info = {
                            "device_id": device_id,
                            "name": device_name,
                            "primary_ip": primary_ip4["address"].split("/")[0],
                            "platform": platform_info.get("name", ""),
                            "network_driver": platform_info["network_driver"],
                        }

                        # Get platform-specific snapshot commands from database
                        device_platform_name = platform_info.get("name", "")

                        # Map Nautobot platform names to CommandPlatform enum
                        # Order matters: check more specific patterns first (e.g., "ios xe" before "ios")
                        platform_mapping = [
                            (["cisco_xe", "ios-xe", "iosxe", "ios xe"], CommandPlatform.IOS_XE),
                            (["cisco_nxos", "nxos", "nx-os", "nexus"], CommandPlatform.NEXUS),
                            (["cisco_ios", "ios"], CommandPlatform.IOS),
                        ]

                        # Try to match platform (case-insensitive)
                        # Check more specific patterns first
                        command_platform = None
                        device_platform_lower = device_platform_name.lower()
                        for patterns, platform_enum in platform_mapping:
                            if any(pattern in device_platform_lower for pattern in patterns):
                                command_platform = platform_enum
                                break

                        # load commands from database
                        if command_platform:
                            # Load snapshot commands for this platform from database
                            snapshot_commands = (
                                db.query(DeviceCommand)
                                .filter(
                                    DeviceCommand.type == CommandType.SNAPSHOT,
                                    DeviceCommand.platform == command_platform,
                                )
                                .all()
                            )
                            commands_to_run = [cmd.command for cmd in snapshot_commands]
                            logger.info(
                                f"Device {device_name} (platform: {command_platform.value}): "
                                f"Loaded {len(commands_to_run)} snapshot commands from database"
                            )
                        else:
                            # No matching platform found
                            error_msg = f"Could not map device platform '{device_platform_name}' to a known CommandPlatform"
                            logger.warning(f"Device {device_name}: {error_msg}")
                            errors.append(
                                {
                                    "device_id": device_id,
                                    "device_name": device_name,
                                    "error": error_msg,
                                }
                            )
                            continue

                        if not commands_to_run:
                            logger.warning(
                                f"Device {device_name}: No snapshot commands found for platform {command_platform.value if command_platform else 'unknown'}"
                            )
                            continue

                        # Execute each command and store baseline
                        device_service = DeviceCommunicationService()
                        device_commands_executed = 0

                        # Generate a unique group ID for this snapshot session
                        # All commands executed in this session will share the same group_id
                        snapshot_group_id = str(uuid.uuid4())
                        logger.info(f"Device {device_name}: Generated snapshot_group_id: {snapshot_group_id}")

                        for command in commands_to_run:
                            try:
                                # Execute command
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                try:
                                    result = loop.run_until_complete(
                                        device_service.execute_command(
                                            device_info=device_info,
                                            command=command,
                                            username=task_username,
                                            parser="TEXTFSM",
                                        )
                                    )
                                finally:
                                    loop.close()

                                if not result.get("success"):
                                    error_msg = f"Command '{command}' failed: {result.get('error', 'Unknown error')}"
                                    logger.warning(f"Device {device_name}: {error_msg}")
                                    errors.append(
                                        {
                                            "device_id": device_id,
                                            "device_name": device_name,
                                            "command": command,
                                            "error": error_msg,
                                        }
                                    )
                                    continue

                                # Get parsed output
                                output = result.get("output")
                                logger.info(f"Device {device_name}: Command '{command}' - output type: {type(output)}, output value: {output}")

                                if not output or not isinstance(output, list):
                                    logger.warning(
                                        f"Device {device_name}: Command '{command}' returned no structured data (not output={not output}, isinstance={isinstance(output, list)})"
                                    )
                                    continue

                                logger.info(f"Device {device_name}: Command '{command}' - passed validation, proceeding to serialize")
                                # Serialize output to JSON
                                raw_output_json = json.dumps(output, indent=2)
                                logger.info(f"Device {device_name}: Command '{command}' - raw_output_json length: {len(raw_output_json)}")

                                # Create normalized version (remove timestamps, counters, etc.)
                                normalized_output_json = _normalize_output(
                                    output, command
                                )
                                logger.info(f"Device {device_name}: Command '{command}' - normalized_output_json length: {len(normalized_output_json)}")

                                # For baselines: check if one exists and update it
                                # For snapshots: always create a new one (never update existing)
                                if snapshot_type_enum == SnapshotType.BASELINE:
                                    # Baseline mode: Check if snapshot exists for this device/command/type
                                    logger.info(f"Device {device_name}: Checking for existing baseline with device_id={device_id}, command={command}, type={snapshot_type_enum}")
                                    existing_snapshot = (
                                        db.query(Snapshot)
                                        .filter(
                                            and_(
                                                Snapshot.device_id == device_id,
                                                Snapshot.command == command,
                                                Snapshot.type == snapshot_type_enum,
                                            )
                                        )
                                        .first()
                                    )
                                    logger.info(f"Device {device_name}: Existing baseline found: {existing_snapshot is not None}")

                                    if existing_snapshot:
                                        # Update existing baseline
                                        existing_snapshot.raw_output = raw_output_json
                                        existing_snapshot.normalized_output = (
                                            normalized_output_json
                                        )
                                        existing_snapshot.device_name = device_name
                                        existing_snapshot.updated_at = datetime.now(
                                            timezone.utc
                                        )
                                        existing_snapshot.version += 1
                                        if notes:
                                            existing_snapshot.notes = notes
                                        baseline_ids.append(existing_snapshot.id)
                                        logger.info(
                                            f"Updated baseline for {device_name}, command '{command}' (version {existing_snapshot.version})"
                                        )
                                    else:
                                        # Create new baseline
                                        new_snapshot = Snapshot(
                                            device_id=device_id,
                                            device_name=device_name,
                                            command=command,
                                            type=snapshot_type_enum,
                                            raw_output=raw_output_json,
                                            normalized_output=normalized_output_json,
                                            snapshot_group_id=snapshot_group_id,
                                            notes=notes
                                            or f"Initial baseline created on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
                                        )
                                        db.add(new_snapshot)
                                        db.flush()  # Get the ID
                                        baseline_ids.append(new_snapshot.id)
                                        logger.info(
                                            f"Created new baseline for {device_name}, command '{command}'"
                                        )
                                else:
                                    # Snapshot mode: Always create a new snapshot (never update)
                                    logger.info(f"Device {device_name}: Creating new snapshot (always creates new, never updates)")
                                    new_snapshot = Snapshot(
                                        device_id=device_id,
                                        device_name=device_name,
                                        command=command,
                                        type=snapshot_type_enum,
                                        raw_output=raw_output_json,
                                        normalized_output=normalized_output_json,
                                        snapshot_group_id=snapshot_group_id,
                                        notes=notes
                                        or f"Snapshot created on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
                                    )
                                    db.add(new_snapshot)
                                    db.flush()  # Get the ID
                                    baseline_ids.append(new_snapshot.id)
                                    logger.info(
                                        f"Created new snapshot for {device_name}, command '{command}' (ID: {new_snapshot.id})"
                                    )

                                device_commands_executed += 1
                                total_commands_executed += 1

                            except Exception as cmd_error:
                                error_msg = f"Error executing command '{command}': {str(cmd_error)}"
                                logger.error(
                                    f"Device {device_name}: {error_msg}", exc_info=True
                                )
                                errors.append(
                                    {
                                        "device_id": device_id,
                                        "device_name": device_name,
                                        "command": command,
                                        "error": error_msg,
                                    }
                                )

                        # Commit after each device
                        db.commit()

                        if device_commands_executed > 0:
                            devices_processed += 1
                            logger.info(
                                f"Completed baseline for device {device_name}: {device_commands_executed}/{len(commands_to_run)} commands successful"
                            )

                    except Exception as device_error:
                        db.rollback()
                        error_msg = f"Error processing device: {str(device_error)}"
                        logger.error(f"Device {device_id}: {error_msg}", exc_info=True)
                        errors.append({"device_id": device_id, "error": error_msg})

                # Final progress update
                task_self.update_state(
                    state="PROGRESS",
                    meta={
                        "current": 100,
                        "total": 100,
                        "status": "Baseline creation completed",
                    },
                )

                result = {
                    "status": "completed",
                    "devices_processed": devices_processed,
                    "total_devices": total_devices,
                    "total_commands": total_commands_executed,
                    "baseline_ids": baseline_ids,
                    "errors": errors,
                    "message": f"Successfully created/updated baselines for {devices_processed}/{total_devices} devices ({total_commands_executed} total commands)",
                }

                logger.info(f"Baseline creation completed: {result['message']}")
                return result

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error in create_baseline task: {str(e)}", exc_info=True)
            task_self.update_state(
                state="FAILURE",
                meta={
                    "error": str(e),
                    "status": "Failed to create baseline",
                },
            )
            raise

    @celery_app.task(bind=True, name="app.tasks.baseline_tasks.create_baseline")
    def create_baseline(
        self,
        device_ids: Optional[List[str]] = None,
        inventory_id: Optional[int] = None,
        commands: Optional[List[str]] = None,
        notes: Optional[str] = None,
        auth_token: str = "",
        username: Optional[str] = None,
        snapshot_type: str = "baseline",
    ):
        """Create or update baselines for devices."""
        return _execute_snapshot_task(
            self,
            device_ids=device_ids,
            inventory_id=inventory_id,
            commands=commands,
            notes=notes,
            auth_token=auth_token,
            username=username,
            snapshot_type=snapshot_type,
        )

    @celery_app.task(bind=True, name="app.tasks.baseline_tasks.create_snapshot")
    def create_snapshot(
        self,
        device_ids: Optional[List[str]] = None,
        inventory_id: Optional[int] = None,
        commands: Optional[List[str]] = None,
        notes: Optional[str] = None,
        auth_token: str = "",
        username: Optional[str] = None,
    ):
        """Create or update snapshots for devices."""
        return _execute_snapshot_task(
            self,
            device_ids=device_ids,
            inventory_id=inventory_id,
            commands=commands,
            notes=notes,
            auth_token=auth_token,
            username=username,
            snapshot_type="snapshot",
        )

    return {
        "create_baseline": create_baseline,
        "create_snapshot": create_snapshot,
    }


def _get_username_from_token(auth_token: str) -> str:
    """
    Extract username from JWT token.

    Args:
        auth_token: JWT authentication token

    Returns:
        Username extracted from token, or 'admin' as fallback
    """
    try:
        from jose import jwt
        from ..core.config import settings

        payload = jwt.decode(
            auth_token, settings.secret_key, algorithms=[settings.algorithm]
        )
        return payload.get("sub", "admin")
    except Exception as e:
        logger.warning(f"Could not decode token: {e}, using default username 'admin'")
        return "admin"


def _normalize_output(output: List[Dict[str, Any]], command: str) -> str:
    """
    Normalize command output for comparison by removing dynamic values.

    This function removes or normalizes:
    - Timestamps and uptime values
    - Packet/byte counters
    - Rate statistics
    - Dynamic status changes
    - Whitespace inconsistencies

    Args:
        output: Parsed command output (list of dicts from TextFSM)
        command: The command that was executed

    Returns:
        JSON string of normalized output
    """
    import copy

    # Create deep copy to avoid modifying original
    normalized = copy.deepcopy(output)

    # Fields to remove based on command type (these are dynamic and shouldn't affect baseline comparison)
    dynamic_fields = {
        "show interfaces": [
            "input_rate",
            "output_rate",
            "input_packets",
            "output_packets",
            "input_bytes",
            "output_bytes",
            "input_errors",
            "output_errors",
            "crc",
            "collisions",
            "interface_resets",
            "last_input",
            "last_output",
            "last_clearing",
            "queue_strategy",
        ],
        "show ip arp": [
            "age"  # ARP age changes constantly
        ],
        "show cdp neighbors": [
            "holdtime"  # CDP holdtime counts down
        ],
        "show mac address-table": [
            # MAC table is generally stable, but we might want to remove port security counters
        ],
        "show ip route": [
            # Routes are generally stable, but we could remove metric values if needed
        ],
    }

    # Determine which fields to remove
    fields_to_remove = []
    for cmd_pattern, fields in dynamic_fields.items():
        if cmd_pattern in command.lower():
            fields_to_remove = fields
            break

    # Remove dynamic fields from each entry
    for entry in normalized:
        if isinstance(entry, dict):
            for field in fields_to_remove:
                entry.pop(field, None)

            # Normalize string values (strip whitespace, lowercase where appropriate)
            for key, value in entry.items():
                if isinstance(value, str):
                    entry[key] = value.strip()

    # Sort list for consistent ordering (helps with comparison)
    # Sort by first available key that seems like an identifier
    if normalized and isinstance(normalized[0], dict):
        sort_keys = [
            "interface",
            "name",
            "network",
            "destination",
            "neighbor",
            "address",
            "mac_address",
        ]
        for sort_key in sort_keys:
            if sort_key in normalized[0]:
                try:
                    normalized = sorted(normalized, key=lambda x: x.get(sort_key, ""))
                    break
                except Exception:
                    pass  # Skip if sorting fails

    return json.dumps(normalized, indent=2, sort_keys=True)
