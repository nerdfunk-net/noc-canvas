"""
Topology Discovery Module.

This module provides topology discovery functionality with separate implementations
for async (API/foreground) and sync (Celery/background) execution paths.

Architecture:
- base.py: Shared constants and utilities used by both paths
- async_discovery.py: HTTP-based discovery for API requests (foreground)
- sync_discovery.py: Direct SSH-based discovery for Celery workers (background)
"""

from .async_discovery import AsyncTopologyDiscoveryService
from .sync_discovery import SyncTopologyDiscoveryService
from .base import TopologyDiscoveryBase

__all__ = [
    "AsyncTopologyDiscoveryService",
    "SyncTopologyDiscoveryService",
    "TopologyDiscoveryBase",
]
