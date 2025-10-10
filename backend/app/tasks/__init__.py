"""
Background tasks package.

This package contains all Celery background tasks organized by functionality:
- nautobot_tasks: Nautobot device synchronization tasks
- checkmk_tasks: CheckMK host management and bulk operations
- cache_tasks: Cache warming tasks
- cleanup_tasks: Data cleanup and maintenance tasks
- test_tasks: Testing and verification tasks
- baseline_tasks: Device configuration baseline and drift detection
- topology_tasks: Network topology discovery tasks
"""

from .topology_tasks import discover_topology_task, discover_single_device_task

__all__ = ["discover_topology_task", "discover_single_device_task"]
