"""
CheckMK synchronization and operations tasks.

This module contains Celery tasks for syncing and managing CheckMK hosts.
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


def register_tasks(celery_app):
    """Register CheckMK tasks with the Celery app."""

    @celery_app.task(bind=True, name="app.tasks.checkmk_tasks.sync_checkmk_hosts")
    def sync_checkmk_hosts(self, filters: Optional[Dict[str, Any]] = None):
        """
        Sync hosts from CheckMK.

        Args:
            filters: Optional filters for host query
                - effective_attributes: Include effective attributes
                - include_links: Include links in response
                - site: Specific site to query

        Returns:
            Dictionary with sync results including host count and status
        """
        try:
            from ..services.checkmk import checkmk_service

            self.update_state(state="PROGRESS", meta={"current": 0, "total": 100})

            # Get hosts from CheckMK
            result = checkmk_service.get_all_hosts(
                effective_attributes=filters.get("effective_attributes", False)
                if filters
                else False,
                include_links=filters.get("include_links", False) if filters else False,
                site=filters.get("site") if filters else None,
            )

            hosts = result.get("value", [])
            total_hosts = len(hosts)

            self.update_state(
                state="PROGRESS",
                meta={
                    "current": 50,
                    "total": 100,
                    "status": f"Retrieved {total_hosts} hosts from CheckMK",
                },
            )

            # Process hosts
            processed_count = 0
            for i, host in enumerate(hosts):
                # Simulate processing
                processed_count += 1
                if i % 10 == 0:  # Update every 10 hosts
                    progress = 50 + int((i / total_hosts) * 50)
                    self.update_state(
                        state="PROGRESS",
                        meta={
                            "current": progress,
                            "total": 100,
                            "status": f"Processed {processed_count}/{total_hosts} hosts",
                        },
                    )

            logger.info(f"Successfully synced {processed_count} hosts from CheckMK")

            return {
                "status": "completed",
                "hosts_processed": processed_count,
                "total_hosts": total_hosts,
                "message": f"Successfully synced {processed_count} hosts from CheckMK",
            }

        except Exception as e:
            logger.error(f"Error in sync_checkmk_hosts task: {str(e)}")
            self.update_state(
                state="FAILURE",
                meta={
                    "error": str(e),
                    "status": "Failed to sync hosts from CheckMK",
                },
            )
            raise

    @celery_app.task(bind=True, name="app.tasks.checkmk_tasks.bulk_host_operations")
    def bulk_host_operations(self, operation: str, hosts_data: List[Dict[str, Any]]):
        """
        Perform bulk operations on CheckMK hosts.

        Args:
            operation: Operation to perform ('create', 'update', 'delete')
            hosts_data: List of host data dictionaries

        Returns:
            Dictionary with operation results
        """
        try:
            from ..services.checkmk import checkmk_service

            total_hosts = len(hosts_data)
            self.update_state(
                state="PROGRESS",
                meta={
                    "current": 0,
                    "total": 100,
                    "status": f"Starting bulk {operation} for {total_hosts} hosts",
                },
            )

            if operation == "create":
                result = checkmk_service.bulk_create_hosts(hosts_data)
            elif operation == "update":
                result = checkmk_service.bulk_update_hosts(hosts_data)
            elif operation == "delete":
                hostnames = [
                    host.get("hostname") for host in hosts_data if host.get("hostname")
                ]
                result = checkmk_service.bulk_delete_hosts(hostnames)
            else:
                raise ValueError(f"Unsupported operation: {operation}")

            self.update_state(
                state="PROGRESS",
                meta={
                    "current": 90,
                    "total": 100,
                    "status": f"Bulk {operation} completed, activating changes",
                },
            )

            # Activate changes
            activation_result = checkmk_service.activate_changes()

            logger.info(
                f"Successfully completed bulk {operation} for {total_hosts} hosts"
            )

            return {
                "status": "completed",
                "operation": operation,
                "hosts_affected": total_hosts,
                "checkmk_result": result,
                "activation_result": activation_result,
                "message": f"Successfully completed bulk {operation} for {total_hosts} hosts",
            }

        except Exception as e:
            logger.error(f"Error in bulk_host_operations task: {str(e)}")
            self.update_state(
                state="FAILURE",
                meta={
                    "error": str(e),
                    "status": f"Failed to perform bulk {operation}",
                },
            )
            raise

    return {
        "sync_checkmk_hosts": sync_checkmk_hosts,
        "bulk_host_operations": bulk_host_operations,
    }
