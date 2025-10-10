"""
Baseline tasks for capturing device configuration snapshots.

This module contains Celery tasks for creating and updating baseline configurations
for network devices. Baselines are used for configuration drift detection, compliance
checking, and change management.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import and_

logger = logging.getLogger(__name__)


def register_tasks(celery_app):
    """Register baseline tasks with the Celery app."""

    @celery_app.task(bind=True, name='app.tasks.baseline_tasks.create_baseline')
    def create_baseline(
        self,
        device_ids: Optional[List[str]] = None,
        inventory_id: Optional[int] = None,
        commands: Optional[List[str]] = None,
        notes: Optional[str] = None,
        auth_token: str = ""
    ):
        """
        Create or update baseline configurations for devices.
        
        This task executes all topology-related commands on devices and stores
        the output as baseline data for future comparison. It reuses the topology
        discovery infrastructure to gather data.
        
        Commands executed by default:
        - show interfaces (Interface states and configuration)
        - show ip arp (ARP table)
        - show cdp neighbors (CDP neighbor information)
        - show mac address-table (MAC address table)
        - show ip route static (Static routes)
        - show ip route ospf (OSPF routes)
        - show ip route bgp (BGP routes)
        
        Args:
            device_ids: List of device IDs to baseline. If None, baselines all devices.
            inventory_id: ID of inventory to use for device selection. Takes precedence over device_ids.
            commands: List of specific commands to execute. If None, runs all default commands.
            notes: Optional notes to store with baseline (e.g., "Pre-upgrade baseline")
            auth_token: Authentication token for device access
            
        Returns:
            Dictionary with baseline creation results:
                - status: "completed" or "failed"
                - devices_processed: Number of devices successfully baselined
                - total_devices: Total number of devices attempted
                - total_commands: Total commands executed
                - errors: List of errors encountered
                - baseline_ids: List of created baseline record IDs
        """
        from ..core.database import SessionLocal
        from ..models.device_cache import BaselineCache
        from ..models.inventory import Inventory
        from ..services.nautobot import nautobot_service
        from ..services.device_communication import DeviceCommunicationService
        from ..services.inventory import preview_inventory
        
        logger.info(f"Starting baseline creation task")
        
        try:
            self.update_state(state="PROGRESS", meta={"current": 0, "total": 100, "status": "Initializing"})
            
            # Default commands to execute for baseline
            default_commands = [
                "show interfaces",
                "show ip arp",
                "show cdp neighbors",
                "show mac address-table",
                "show ip route static",
                "show ip route ospf",
                "show ip route bgp",
            ]
            
            # Use provided commands or default
            commands_to_run = commands if commands else default_commands
            
            # Get username from token
            username = _get_username_from_token(auth_token)
            
            # Initialize database session
            db = SessionLocal()
            
            try:
                # Get devices to baseline
                # Priority: inventory_id > device_ids > all devices
                if inventory_id:
                    # Resolve inventory to device IDs
                    self.update_state(
                        state="PROGRESS",
                        meta={"current": 3, "total": 100, "status": f"Resolving inventory {inventory_id} to devices"}
                    )
                    
                    inventory = db.query(Inventory).filter(Inventory.id == inventory_id).first()
                    if not inventory:
                        raise ValueError(f"Inventory {inventory_id} not found")
                    
                    # Use inventory service to preview devices
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        devices_result = loop.run_until_complete(
                            preview_inventory(db, inventory.id, username)
                        )
                        device_ids = [d['id'] for d in devices_result.get('devices', [])]
                        logger.info(f"Resolved inventory '{inventory.name}' to {len(device_ids)} devices")
                    finally:
                        loop.close()
                    
                    if not device_ids:
                        logger.warning(f"Inventory '{inventory.name}' resolved to zero devices")
                        return {
                            "status": "completed",
                            "devices_processed": 0,
                            "total_devices": 0,
                            "total_commands": 0,
                            "baseline_ids": [],
                            "errors": [],
                            "message": f"Inventory '{inventory.name}' contains no devices"
                        }
                
                if not device_ids:
                    # Get all devices from Nautobot if none specified
                    self.update_state(
                        state="PROGRESS",
                        meta={"current": 5, "total": 100, "status": "Fetching devices from Nautobot"}
                    )
                    
                    # Run async function in event loop
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        devices_result = loop.run_until_complete(
                            nautobot_service.get_devices_async(username, limit=1000)
                        )
                        device_ids = [d['id'] for d in devices_result.get('devices', [])]
                    finally:
                        loop.close()
                
                total_devices = len(device_ids)
                total_commands = len(commands_to_run)
                logger.info(f"Baselining {total_devices} devices with {total_commands} commands each")
                
                devices_processed = 0
                total_commands_executed = 0
                errors = []
                baseline_ids = []
                
                # Process each device
                for device_index, device_id in enumerate(device_ids):
                    try:
                        # Update progress
                        progress = 10 + int((device_index / total_devices) * 80)
                        self.update_state(
                            state="PROGRESS",
                            meta={
                                "current": progress,
                                "total": 100,
                                "status": f"Processing device {device_index + 1}/{total_devices}",
                                "devices_processed": devices_processed,
                                "total_commands_executed": total_commands_executed
                            }
                        )
                        
                        # Get device info from Nautobot
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            device_data = loop.run_until_complete(
                                nautobot_service.get_device(device_id, username)
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
                            errors.append({"device_id": device_id, "device_name": device_name, "error": error_msg})
                            continue
                        
                        platform_info = device_data.get("platform")
                        if not platform_info or not platform_info.get("network_driver"):
                            error_msg = f"Device {device_name} does not have platform/network_driver configured"
                            logger.warning(error_msg)
                            errors.append({"device_id": device_id, "device_name": device_name, "error": error_msg})
                            continue
                        
                        # Prepare device info for command execution
                        device_info = {
                            "device_id": device_id,
                            "name": device_name,
                            "primary_ip": primary_ip4["address"].split("/")[0],
                            "platform": platform_info.get("name", ""),
                            "network_driver": platform_info["network_driver"],
                        }
                        
                        # Execute each command and store baseline
                        device_service = DeviceCommunicationService()
                        device_commands_executed = 0
                        
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
                                            username=username,
                                            parser="TEXTFSM"
                                        )
                                    )
                                finally:
                                    loop.close()
                                
                                if not result.get("success"):
                                    error_msg = f"Command '{command}' failed: {result.get('error', 'Unknown error')}"
                                    logger.warning(f"Device {device_name}: {error_msg}")
                                    errors.append({
                                        "device_id": device_id,
                                        "device_name": device_name,
                                        "command": command,
                                        "error": error_msg
                                    })
                                    continue
                                
                                # Get parsed output
                                output = result.get("output")
                                if not output or not isinstance(output, list):
                                    logger.warning(f"Device {device_name}: Command '{command}' returned no structured data")
                                    continue
                                
                                # Serialize output to JSON
                                raw_output_json = json.dumps(output, indent=2)
                                
                                # Create normalized version (remove timestamps, counters, etc.)
                                normalized_output_json = _normalize_output(output, command)
                                
                                # Check if baseline exists for this device/command
                                existing_baseline = db.query(BaselineCache).filter(
                                    and_(
                                        BaselineCache.device_id == device_id,
                                        BaselineCache.command == command
                                    )
                                ).first()
                                
                                if existing_baseline:
                                    # Update existing baseline
                                    existing_baseline.raw_output = raw_output_json
                                    existing_baseline.normalized_output = normalized_output_json
                                    existing_baseline.device_name = device_name
                                    existing_baseline.updated_at = datetime.now(timezone.utc)
                                    existing_baseline.baseline_version += 1
                                    if notes:
                                        existing_baseline.notes = notes
                                    baseline_ids.append(existing_baseline.id)
                                    logger.info(f"Updated baseline for {device_name}, command '{command}' (version {existing_baseline.baseline_version})")
                                else:
                                    # Create new baseline
                                    new_baseline = BaselineCache(
                                        device_id=device_id,
                                        device_name=device_name,
                                        command=command,
                                        raw_output=raw_output_json,
                                        normalized_output=normalized_output_json,
                                        notes=notes or f"Initial baseline created on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
                                    )
                                    db.add(new_baseline)
                                    db.flush()  # Get the ID
                                    baseline_ids.append(new_baseline.id)
                                    logger.info(f"Created new baseline for {device_name}, command '{command}'")
                                
                                device_commands_executed += 1
                                total_commands_executed += 1
                                
                            except Exception as cmd_error:
                                error_msg = f"Error executing command '{command}': {str(cmd_error)}"
                                logger.error(f"Device {device_name}: {error_msg}", exc_info=True)
                                errors.append({
                                    "device_id": device_id,
                                    "device_name": device_name,
                                    "command": command,
                                    "error": error_msg
                                })
                        
                        # Commit after each device
                        db.commit()
                        
                        if device_commands_executed > 0:
                            devices_processed += 1
                            logger.info(f"Completed baseline for device {device_name}: {device_commands_executed}/{total_commands} commands successful")
                        
                    except Exception as device_error:
                        db.rollback()
                        error_msg = f"Error processing device: {str(device_error)}"
                        logger.error(f"Device {device_id}: {error_msg}", exc_info=True)
                        errors.append({
                            "device_id": device_id,
                            "error": error_msg
                        })
                
                # Final progress update
                self.update_state(state="PROGRESS", meta={"current": 100, "total": 100, "status": "Baseline creation completed"})
                
                result = {
                    "status": "completed",
                    "devices_processed": devices_processed,
                    "total_devices": total_devices,
                    "total_commands": total_commands_executed,
                    "baseline_ids": baseline_ids,
                    "errors": errors,
                    "message": f"Successfully created/updated baselines for {devices_processed}/{total_devices} devices ({total_commands_executed} total commands)"
                }
                
                logger.info(f"Baseline creation completed: {result['message']}")
                return result
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error in create_baseline task: {str(e)}", exc_info=True)
            self.update_state(
                state="FAILURE",
                meta={
                    "error": str(e),
                    "status": "Failed to create baseline",
                },
            )
            raise

    return {
        'create_baseline': create_baseline,
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
            "input_rate", "output_rate", "input_packets", "output_packets",
            "input_bytes", "output_bytes", "input_errors", "output_errors",
            "crc", "collisions", "interface_resets", "last_input", "last_output",
            "last_clearing", "queue_strategy"
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
        ]
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
        sort_keys = ['interface', 'name', 'network', 'destination', 'neighbor', 'address', 'mac_address']
        for sort_key in sort_keys:
            if sort_key in normalized[0]:
                try:
                    normalized = sorted(normalized, key=lambda x: x.get(sort_key, ''))
                    break
                except:
                    pass  # Skip if sorting fails
    
    return json.dumps(normalized, indent=2, sort_keys=True)
