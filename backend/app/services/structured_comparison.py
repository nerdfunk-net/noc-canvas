"""
Structured comparison service for network command outputs.

This service provides semantic comparison of network commands by understanding
the structure of the data, unlike simple text diffs.
"""

import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class StructuredComparator:
    """Service for comparing structured command outputs."""

    @staticmethod
    def compare_show_interfaces(
        baseline_output: str,
        snapshot_output: str
    ) -> Dict[str, Any]:
        """
        Compare 'show interfaces' command outputs.

        Args:
            baseline_output: JSON string of baseline normalized output
            snapshot_output: JSON string of snapshot normalized output

        Returns:
            Dictionary with structured comparison results:
            {
                "command": "show interfaces",
                "interfaces": {
                    "Ethernet0/0": {
                        "status": "changed",
                        "fields": [
                            {
                                "field": "link_status",
                                "baseline": "up",
                                "snapshot": "down",
                                "changed": true
                            },
                            ...
                        ]
                    },
                    ...
                },
                "summary": {
                    "total_interfaces": 4,
                    "added": 0,
                    "removed": 0,
                    "changed": 1,
                    "unchanged": 3
                }
            }
        """
        try:
            # Parse JSON outputs
            baseline_data = json.loads(baseline_output) if isinstance(baseline_output, str) else baseline_output
            snapshot_data = json.loads(snapshot_output) if isinstance(snapshot_output, str) else snapshot_output

            # Convert lists to dictionaries keyed by interface name
            baseline_interfaces = {item["interface"]: item for item in baseline_data}
            snapshot_interfaces = {item["interface"]: item for item in snapshot_data}

            # Get all interface names
            all_interfaces = set(baseline_interfaces.keys()) | set(snapshot_interfaces.keys())
            baseline_only = set(baseline_interfaces.keys()) - set(snapshot_interfaces.keys())
            snapshot_only = set(snapshot_interfaces.keys()) - set(baseline_interfaces.keys())
            common_interfaces = set(baseline_interfaces.keys()) & set(snapshot_interfaces.keys())

            result = {
                "command": "show interfaces",
                "interfaces": {},
                "summary": {
                    "total_interfaces": len(all_interfaces),
                    "added": len(snapshot_only),
                    "removed": len(baseline_only),
                    "changed": 0,
                    "unchanged": 0
                }
            }

            # Process interfaces that only exist in baseline (removed)
            for interface_name in baseline_only:
                baseline_iface = baseline_interfaces[interface_name]
                result["interfaces"][interface_name] = {
                    "status": "removed",
                    "fields": [
                        {
                            "field": field,
                            "baseline": value,
                            "snapshot": None,
                            "changed": True
                        }
                        for field, value in baseline_iface.items()
                        if field != "interface"
                    ]
                }

            # Process interfaces that only exist in snapshot (added)
            for interface_name in snapshot_only:
                snapshot_iface = snapshot_interfaces[interface_name]
                result["interfaces"][interface_name] = {
                    "status": "added",
                    "fields": [
                        {
                            "field": field,
                            "baseline": None,
                            "snapshot": value,
                            "changed": True
                        }
                        for field, value in snapshot_iface.items()
                        if field != "interface"
                    ]
                }

            # Process common interfaces
            for interface_name in common_interfaces:
                baseline_iface = baseline_interfaces[interface_name]
                snapshot_iface = snapshot_interfaces[interface_name]

                # Get all fields from both
                all_fields = set(baseline_iface.keys()) | set(snapshot_iface.keys())
                all_fields.discard("interface")  # Don't include the interface name itself

                fields_comparison = []
                has_changes = False

                for field in sorted(all_fields):
                    baseline_value = baseline_iface.get(field)
                    snapshot_value = snapshot_iface.get(field)
                    changed = baseline_value != snapshot_value

                    if changed:
                        has_changes = True

                    fields_comparison.append({
                        "field": field,
                        "baseline": baseline_value,
                        "snapshot": snapshot_value,
                        "changed": changed
                    })

                result["interfaces"][interface_name] = {
                    "status": "changed" if has_changes else "unchanged",
                    "fields": fields_comparison
                }

                if has_changes:
                    result["summary"]["changed"] += 1
                else:
                    result["summary"]["unchanged"] += 1

            return result

        except Exception as e:
            logger.error(f"Error comparing show interfaces: {str(e)}")
            raise

    @staticmethod
    def compare_show_ip_route_static(
        baseline_output: str,
        snapshot_output: str
    ) -> Dict[str, Any]:
        """
        Compare 'show ip route static' command outputs.

        Args:
            baseline_output: JSON string of baseline normalized output
            snapshot_output: JSON string of snapshot normalized output

        Returns:
            Dictionary with structured comparison results grouped by network/prefix
        """
        try:
            # Parse JSON outputs
            baseline_data = json.loads(baseline_output) if isinstance(baseline_output, str) else baseline_output
            snapshot_data = json.loads(snapshot_output) if isinstance(snapshot_output, str) else snapshot_output

            # Convert lists to dictionaries keyed by network/prefix combination
            baseline_routes = {
                f"{item['network']}/{item['prefix_length']}": item
                for item in baseline_data
            }
            snapshot_routes = {
                f"{item['network']}/{item['prefix_length']}": item
                for item in snapshot_data
            }

            # Get all route keys
            all_routes = set(baseline_routes.keys()) | set(snapshot_routes.keys())
            baseline_only = set(baseline_routes.keys()) - set(snapshot_routes.keys())
            snapshot_only = set(snapshot_routes.keys()) - set(baseline_routes.keys())
            common_routes = set(baseline_routes.keys()) & set(snapshot_routes.keys())

            result = {
                "command": "show ip route static",
                "routes": {},
                "summary": {
                    "total_routes": len(all_routes),
                    "added": len(snapshot_only),
                    "removed": len(baseline_only),
                    "changed": 0,
                    "unchanged": 0
                }
            }

            # Process routes that only exist in baseline (removed)
            for route_key in baseline_only:
                baseline_route = baseline_routes[route_key]
                result["routes"][route_key] = {
                    "status": "removed",
                    "fields": [
                        {
                            "field": field,
                            "baseline": value,
                            "snapshot": None,
                            "changed": True
                        }
                        for field, value in baseline_route.items()
                        if field not in ["network", "prefix_length", "uptime"]
                    ]
                }

            # Process routes that only exist in snapshot (added)
            for route_key in snapshot_only:
                snapshot_route = snapshot_routes[route_key]
                result["routes"][route_key] = {
                    "status": "added",
                    "fields": [
                        {
                            "field": field,
                            "baseline": None,
                            "snapshot": value,
                            "changed": True
                        }
                        for field, value in snapshot_route.items()
                        if field not in ["network", "prefix_length", "uptime"]
                    ]
                }

            # Process common routes
            for route_key in common_routes:
                baseline_route = baseline_routes[route_key]
                snapshot_route = snapshot_routes[route_key]

                # Get all fields from both, excluding network, prefix_length, and uptime
                all_fields = set(baseline_route.keys()) | set(snapshot_route.keys())
                all_fields.discard("network")
                all_fields.discard("prefix_length")
                all_fields.discard("uptime")

                fields_comparison = []
                has_changes = False

                for field in sorted(all_fields):
                    baseline_value = baseline_route.get(field)
                    snapshot_value = snapshot_route.get(field)
                    changed = baseline_value != snapshot_value

                    if changed:
                        has_changes = True

                    fields_comparison.append({
                        "field": field,
                        "baseline": baseline_value,
                        "snapshot": snapshot_value,
                        "changed": changed
                    })

                result["routes"][route_key] = {
                    "status": "changed" if has_changes else "unchanged",
                    "fields": fields_comparison
                }

                if has_changes:
                    result["summary"]["changed"] += 1
                else:
                    result["summary"]["unchanged"] += 1

            return result

        except Exception as e:
            logger.error(f"Error comparing show ip route static: {str(e)}")
            raise

    @staticmethod
    def compare(
        command: str,
        baseline_output: str,
        snapshot_output: str
    ) -> Optional[Dict[str, Any]]:
        """
        Compare command outputs based on command type.

        Args:
            command: Command name (e.g., "show interfaces")
            baseline_output: Baseline normalized output (JSON string)
            snapshot_output: Snapshot normalized output (JSON string)

        Returns:
            Structured comparison result or None if command not supported
        """
        # Normalize command name
        command_lower = command.lower().strip()

        # Route to appropriate comparator
        if "show interfaces" in command_lower or "show interface" in command_lower:
            return StructuredComparator.compare_show_interfaces(
                baseline_output,
                snapshot_output
            )
        elif "show ip route static" in command_lower:
            return StructuredComparator.compare_show_ip_route_static(
                baseline_output,
                snapshot_output
            )
        elif "show ip route ospf" in command_lower:
            # OSPF routes use the same structure as static routes
            result = StructuredComparator.compare_show_ip_route_static(
                baseline_output,
                snapshot_output
            )
            # Update command name in result
            result["command"] = "show ip route ospf"
            return result

        # Add more command parsers here as needed
        # elif "show version" in command_lower:
        #     return StructuredComparator.compare_show_version(...)

        # Command not supported for structured comparison
        return None
