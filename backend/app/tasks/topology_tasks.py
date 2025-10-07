"""
Celery tasks for topology discovery.

This module contains Celery tasks for discovering network topology data
from devices in the background. Tasks run in Celery workers and support
parallel execution, progress tracking, and automatic retries.
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from celery import group

from app.services.background_jobs import celery_app
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_kwargs={'max_retries': 3, 'countdown': 5},
    retry_backoff=True,
    time_limit=300,  # 5 minutes per device
    soft_time_limit=240
)
def discover_single_device_task(
    self,
    device_id: str,
    parent_job_id: str,
    options: Dict[str, Any],
    auth_token: str
):
    """
    Discover topology data for a single device.
    
    This task:
    - Calls device endpoints to collect topology data
    - Updates progress via Celery state
    - Caches results if requested
    - Handles errors gracefully with retries
    
    Args:
        device_id: Device ID to discover
        parent_job_id: Parent task ID for correlation
        options: Dictionary with discovery options:
            - include_static_routes: bool
            - include_ospf_routes: bool
            - include_bgp_routes: bool
            - include_mac_table: bool
            - include_cdp_neighbors: bool
            - cache_results: bool
        auth_token: Authentication token for API calls
        
    Returns:
        Dictionary with discovery results:
            - device_id: str
            - success: bool
            - data: dict (if successful)
            - error: str (if failed)
    """
    logger.info(f"🔍 Starting discovery for device {device_id} (job: {parent_job_id})")
    
    # Update initial state
    self.update_state(
        state='PROGRESS',
        meta={
            'device_id': device_id,
            'parent_job_id': parent_job_id,
            'status': 'in_progress',
            'progress': 0,
            'current_task': 'Initializing',
            'started_at': datetime.now(timezone.utc).isoformat()
        }
    )
    
    # Create database session for this task
    db = SessionLocal()
    
    try:
        # Import here to avoid circular imports
        from app.services.topology_discovery.sync_discovery import SyncTopologyDiscoveryService
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={
                'device_id': device_id,
                'status': 'in_progress',
                'progress': 10,
                'current_task': 'Starting device discovery'
            }
        )
        
        # Call synchronous discovery service
        device_data = SyncTopologyDiscoveryService.discover_device_data_sync(
            db=db,
            device_id=device_id,
            task=self,  # Pass task for progress updates
            include_static_routes=options.get('include_static_routes', True),
            include_ospf_routes=options.get('include_ospf_routes', True),
            include_bgp_routes=options.get('include_bgp_routes', True),
            include_mac_table=options.get('include_mac_table', True),
            include_cdp_neighbors=options.get('include_cdp_neighbors', True),
            include_arp=options.get('include_arp', True),
            include_interfaces=options.get('include_interfaces', True),
            cache_results=options.get('cache_results', True),
            auth_token=auth_token
        )
        
        # Commit database changes
        db.commit()
        
        # Final progress update
        self.update_state(
            state='PROGRESS',
            meta={
                'device_id': device_id,
                'status': 'completed',
                'progress': 100,
                'current_task': 'Discovery completed',
                'completed_at': datetime.now(timezone.utc).isoformat()
            }
        )
        
        logger.info(f"✅ Discovery completed for device {device_id}")
        
        return {
            'device_id': device_id,
            'success': True,
            'data': device_data,
            'error': None
        }
        
    except Exception as e:
        db.rollback()
        error_msg = str(e)
        logger.error(f"❌ Discovery failed for device {device_id}: {error_msg}", exc_info=True)
        
        # Update error state
        self.update_state(
            state='PROGRESS',
            meta={
                'device_id': device_id,
                'status': 'failed',
                'progress': 0,
                'current_task': None,
                'error': error_msg,
                'completed_at': datetime.now(timezone.utc).isoformat()
            }
        )
        
        return {
            'device_id': device_id,
            'success': False,
            'data': None,
            'error': error_msg
        }
        
    finally:
        db.close()


@celery_app.task(bind=True)
def discover_topology_task(
    self,
    device_ids: List[str],
    include_static_routes: bool = True,
    include_ospf_routes: bool = True,
    include_bgp_routes: bool = True,
    include_mac_table: bool = True,
    include_cdp_neighbors: bool = True,
    include_arp: bool = True,
    include_interfaces: bool = True,
    cache_results: bool = True,
    auth_token: str = ""
):
    """
    Main orchestrator task for discovering topology from multiple devices.
    
    This task:
    - Creates parallel sub-tasks for each device
    - Monitors overall progress
    - Aggregates results from all devices
    - Returns comprehensive results
    
    Args:
        device_ids: List of device IDs to discover
        include_static_routes: Whether to collect static routes
        include_ospf_routes: Whether to collect OSPF routes
        include_bgp_routes: Whether to collect BGP routes
        include_mac_table: Whether to collect MAC address table
        include_cdp_neighbors: Whether to collect CDP neighbors
        include_arp: Whether to collect ARP entries
        cache_results: Whether to cache results to database
        auth_token: Authentication token for API calls
        
    Returns:
        Dictionary with discovery results:
            - job_id: str
            - status: str
            - total_devices: int
            - successful_devices: int
            - failed_devices: int
            - devices_data: dict
            - errors: dict
            - started_at: str
            - completed_at: str
            - duration_seconds: float
    """
    total_devices = len(device_ids)
    start_time = datetime.now(timezone.utc)
    
    logger.info(f"🚀 Starting topology discovery orchestrator")
    logger.info(f"   Job ID: {self.request.id}")
    logger.info(f"   Devices: {total_devices}")
    logger.info(f"   Device IDs: {device_ids}")
    
    # Initialize state
    self.update_state(
        state='PROGRESS',
        meta={
            'job_id': self.request.id,
            'status': 'in_progress',
            'total_devices': total_devices,
            'completed_devices': 0,
            'failed_devices': 0,
            'progress_percentage': 0,
            'devices': [
                {
                    'device_id': device_id,
                    'status': 'pending',
                    'progress_percentage': 0,
                    'current_task': None,
                    'error': None,
                    'started_at': None,
                    'completed_at': None
                }
                for device_id in device_ids
            ],
            'started_at': start_time.isoformat(),
            'completed_at': None
        }
    )
    
    # Create options dict for sub-tasks
    options = {
        'include_static_routes': include_static_routes,
        'include_ospf_routes': include_ospf_routes,
        'include_bgp_routes': include_bgp_routes,
        'include_mac_table': include_mac_table,
        'include_cdp_neighbors': include_cdp_neighbors,
        'include_arp': include_arp,
        'include_interfaces': include_interfaces,
        'cache_results': cache_results
    }
    
    try:
        # Create parallel device discovery tasks using Celery groups
        logger.info(f"📦 Creating group of {total_devices} parallel tasks")
        
        job = group(
            discover_single_device_task.s(
                device_id=device_id,
                parent_job_id=self.request.id,
                options=options,
                auth_token=auth_token
            )
            for device_id in device_ids
        )
        
        # Execute parallel tasks - DO NOT call .get() within a task!
        logger.info("🔄 Executing parallel tasks...")
        result = job.apply_async()
        
        # Store the group result ID for progress tracking
        # The API endpoint will query individual task results
        logger.info(f"✅ Group dispatched with result ID: {result.id}")
        
        # Return immediately with group info
        # The API will track progress by querying the group result
        return {
            'status': 'in_progress',
            'job_id': self.request.id,
            'group_id': result.id,
            'total_devices': total_devices,
            'device_ids': device_ids,
            'message': f'Dispatched {total_devices} parallel discovery tasks',
            'started_at': start_time.isoformat()
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Discovery orchestrator failed: {error_msg}", exc_info=True)
        
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        
        # Update error state
        self.update_state(
            state='FAILURE',
            meta={
                'job_id': self.request.id,
                'status': 'failed',
                'error': error_msg,
                'total_devices': total_devices,
                'completed_at': end_time.isoformat(),
                'duration_seconds': duration
            }
        )
        
        raise

