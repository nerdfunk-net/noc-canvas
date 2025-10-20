"""
Structured comparison service for network command outputs.

This service provides semantic comparison of network commands by understanding
the structure of the data, unlike simple text diffs.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Callable

logger = logging.getLogger(__name__)


class StructuredComparator:
    """Service for comparing structured command outputs."""

    @staticmethod
    def _generic_compare(
        baseline_output: str,
        snapshot_output: str,
        key_field: str,
        result_key: str,
        command_name: str,
        exclude_fields: List[str],
        summary_count_key: str,
        key_builder: Optional[Callable[[Dict[str, Any]], str]] = None
    ) -> Dict[str, Any]:
        """
        Generic comparison method for structured data.

        Args:
            baseline_output: JSON string of baseline normalized output
            snapshot_output: JSON string of snapshot normalized output
            key_field: Field name to use as unique key (e.g., "interface", "mac_address")
            result_key: Key name for results dict (e.g., "interfaces", "routes", "arp_entries")
            command_name: Command name for result (e.g., "show interfaces")
            exclude_fields: List of fields to exclude from comparison
            summary_count_key: Key name for total count in summary (e.g., "total_interfaces")
            key_builder: Optional function to build composite keys from item dict

        Returns:
            Dictionary with structured comparison results
        """
        try:
            # Parse JSON outputs
            baseline_data = json.loads(baseline_output) if isinstance(baseline_output, str) else baseline_output
            snapshot_data = json.loads(snapshot_output) if isinstance(snapshot_output, str) else snapshot_output

            # Build key-value mappings
            if key_builder:
                # Use custom key builder for composite keys
                baseline_items = {key_builder(item): item for item in baseline_data}
                snapshot_items = {key_builder(item): item for item in snapshot_data}
            else:
                # Use simple field as key
                baseline_items = {item[key_field]: item for item in baseline_data}
                snapshot_items = {item[key_field]: item for item in snapshot_data}

            # Calculate set differences
            all_keys = set(baseline_items.keys()) | set(snapshot_items.keys())
            baseline_only = set(baseline_items.keys()) - set(snapshot_items.keys())
            snapshot_only = set(snapshot_items.keys()) - set(baseline_items.keys())
            common_keys = set(baseline_items.keys()) & set(snapshot_items.keys())

            result = {
                "command": command_name,
                result_key: {},
                "summary": {
                    summary_count_key: len(all_keys),
                    "added": len(snapshot_only),
                    "removed": len(baseline_only),
                    "changed": 0,
                    "unchanged": 0
                }
            }

            # Process items that only exist in baseline (removed)
            for item_key in baseline_only:
                baseline_item = baseline_items[item_key]
                result[result_key][item_key] = {
                    "status": "removed",
                    "fields": [
                        {
                            "field": field,
                            "baseline": value,
                            "snapshot": None,
                            "changed": True
                        }
                        for field, value in baseline_item.items()
                        if field not in exclude_fields
                    ]
                }

            # Process items that only exist in snapshot (added)
            for item_key in snapshot_only:
                snapshot_item = snapshot_items[item_key]
                result[result_key][item_key] = {
                    "status": "added",
                    "fields": [
                        {
                            "field": field,
                            "baseline": None,
                            "snapshot": value,
                            "changed": True
                        }
                        for field, value in snapshot_item.items()
                        if field not in exclude_fields
                    ]
                }

            # Process common items
            for item_key in common_keys:
                baseline_item = baseline_items[item_key]
                snapshot_item = snapshot_items[item_key]

                # Get all fields from both, excluding specified fields
                all_fields = set(baseline_item.keys()) | set(snapshot_item.keys())
                for exclude_field in exclude_fields:
                    all_fields.discard(exclude_field)

                fields_comparison = []
                has_changes = False

                for field in sorted(all_fields):
                    baseline_value = baseline_item.get(field)
                    snapshot_value = snapshot_item.get(field)
                    changed = baseline_value != snapshot_value

                    if changed:
                        has_changes = True

                    fields_comparison.append({
                        "field": field,
                        "baseline": baseline_value,
                        "snapshot": snapshot_value,
                        "changed": changed
                    })

                result[result_key][item_key] = {
                    "status": "changed" if has_changes else "unchanged",
                    "fields": fields_comparison
                }

                if has_changes:
                    result["summary"]["changed"] += 1
                else:
                    result["summary"]["unchanged"] += 1

            return result

        except Exception as e:
            logger.error(f"Error comparing {command_name}: {str(e)}")
            raise

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
            Dictionary with structured comparison results
        """
        return StructuredComparator._generic_compare(
            baseline_output=baseline_output,
            snapshot_output=snapshot_output,
            key_field="interface",
            result_key="interfaces",
            command_name="show interfaces",
            exclude_fields=["interface"],
            summary_count_key="total_interfaces"
        )

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
        return StructuredComparator._generic_compare(
            baseline_output=baseline_output,
            snapshot_output=snapshot_output,
            key_field=None,  # Using key_builder instead
            result_key="routes",
            command_name="show ip route static",
            exclude_fields=["network", "prefix_length", "uptime"],
            summary_count_key="total_routes",
            key_builder=lambda item: f"{item['network']}/{item['prefix_length']}"
        )

    @staticmethod
    def compare_show_ip_arp(
        baseline_output: str,
        snapshot_output: str
    ) -> Dict[str, Any]:
        """
        Compare 'show ip arp' command outputs.

        Args:
            baseline_output: JSON string of baseline normalized output
            snapshot_output: JSON string of snapshot normalized output

        Returns:
            Dictionary with structured comparison results grouped by MAC address
        """
        return StructuredComparator._generic_compare(
            baseline_output=baseline_output,
            snapshot_output=snapshot_output,
            key_field="mac_address",
            result_key="arp_entries",
            command_name="show ip arp",
            exclude_fields=["mac_address"],
            summary_count_key="total_entries"
        )

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
        elif "show ip arp" in command_lower:
            return StructuredComparator.compare_show_ip_arp(
                baseline_output,
                snapshot_output
            )

        # Add more command parsers here as needed
        # elif "show version" in command_lower:
        #     return StructuredComparator.compare_show_version(...)

        # Command not supported for structured comparison
        return None
