"""
Baseline comparison utilities.

This module provides utilities for comparing baseline configurations to detect
configuration drift and changes between snapshots.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from ..models.device_cache import BaselineCache

logger = logging.getLogger(__name__)


class BaselineComparator:
    """Utility class for comparing baseline configurations."""
    
    @staticmethod
    def get_latest_baseline(
        db: Session,
        device_id: str,
        command: str
    ) -> Optional[BaselineCache]:
        """
        Get the most recent baseline for a device and command.
        
        Args:
            db: Database session
            device_id: Device UUID
            command: Command name
            
        Returns:
            Latest BaselineCache record or None
        """
        return db.query(BaselineCache).filter(
            and_(
                BaselineCache.device_id == device_id,
                BaselineCache.command == command
            )
        ).order_by(desc(BaselineCache.updated_at)).first()
    
    @staticmethod
    def get_baseline_by_version(
        db: Session,
        device_id: str,
        command: str,
        version: int
    ) -> Optional[BaselineCache]:
        """
        Get a specific baseline version.
        
        Args:
            db: Database session
            device_id: Device UUID
            command: Command name
            version: Baseline version number
            
        Returns:
            BaselineCache record or None
        """
        return db.query(BaselineCache).filter(
            and_(
                BaselineCache.device_id == device_id,
                BaselineCache.command == command,
                BaselineCache.baseline_version == version
            )
        ).first()
    
    @staticmethod
    def get_baseline_history(
        db: Session,
        device_id: str,
        command: str,
        limit: int = 10
    ) -> List[BaselineCache]:
        """
        Get baseline history for a device and command.
        
        Args:
            db: Database session
            device_id: Device UUID
            command: Command name
            limit: Maximum number of records to return
            
        Returns:
            List of BaselineCache records ordered by version desc
        """
        return db.query(BaselineCache).filter(
            and_(
                BaselineCache.device_id == device_id,
                BaselineCache.command == command
            )
        ).order_by(desc(BaselineCache.baseline_version)).limit(limit).all()
    
    @staticmethod
    def compare_baselines(
        baseline_old: BaselineCache,
        baseline_new: BaselineCache,
        use_normalized: bool = True
    ) -> Dict[str, Any]:
        """
        Compare two baseline versions and return differences.
        
        Args:
            baseline_old: Older baseline version
            baseline_new: Newer baseline version
            use_normalized: Use normalized output (recommended) or raw output
            
        Returns:
            Dictionary containing comparison results with structure:
            {
                "baseline_old": {...},
                "baseline_new": {...},
                "has_changes": bool,
                "summary": {...},
                "differences": {...}
            }
        """
        # Select which output to compare
        output_field = "normalized_output" if use_normalized else "raw_output"
        
        old_data = json.loads(getattr(baseline_old, output_field))
        new_data = json.loads(getattr(baseline_new, output_field))
        
        # Calculate differences
        differences = BaselineComparator._calculate_differences(old_data, new_data)
        
        return {
            "baseline_old": {
                "id": baseline_old.id,
                "version": baseline_old.baseline_version,
                "updated_at": baseline_old.updated_at.isoformat(),
                "notes": baseline_old.notes
            },
            "baseline_new": {
                "id": baseline_new.id,
                "version": baseline_new.baseline_version,
                "updated_at": baseline_new.updated_at.isoformat(),
                "notes": baseline_new.notes
            },
            "command": baseline_old.command,
            "device_id": baseline_old.device_id,
            "device_name": baseline_old.device_name,
            "has_changes": differences["has_changes"],
            "summary": differences["summary"],
            "differences": differences["details"]
        }
    
    @staticmethod
    def compare_current_to_baseline(
        db: Session,
        device_id: str,
        command: str,
        current_output: List[Dict[str, Any]],
        baseline_version: Optional[int] = None,
        use_normalized: bool = True
    ) -> Dict[str, Any]:
        """
        Compare current device output to a baseline.
        
        Args:
            db: Database session
            device_id: Device UUID
            command: Command name
            current_output: Current parsed command output
            baseline_version: Specific baseline version to compare. If None, uses latest.
            use_normalized: Use normalized comparison
            
        Returns:
            Comparison results dictionary
        """
        # Get baseline
        if baseline_version is not None:
            baseline = BaselineComparator.get_baseline_by_version(
                db, device_id, command, baseline_version
            )
        else:
            baseline = BaselineComparator.get_latest_baseline(db, device_id, command)
        
        if not baseline:
            return {
                "error": "No baseline found",
                "device_id": device_id,
                "command": command
            }
        
        # Parse baseline data
        output_field = "normalized_output" if use_normalized else "raw_output"
        baseline_data = json.loads(getattr(baseline, output_field))
        
        # Normalize current output if requested
        if use_normalized:
            from ..tasks.baseline_tasks import _normalize_output
            current_output_json = _normalize_output(current_output, command)
            current_data = json.loads(current_output_json)
        else:
            current_data = current_output
        
        # Calculate differences
        differences = BaselineComparator._calculate_differences(baseline_data, current_data)
        
        return {
            "baseline": {
                "id": baseline.id,
                "version": baseline.baseline_version,
                "updated_at": baseline.updated_at.isoformat(),
                "notes": baseline.notes
            },
            "current": {
                "timestamp": datetime.utcnow().isoformat(),
                "command": command
            },
            "command": command,
            "device_id": device_id,
            "device_name": baseline.device_name,
            "has_changes": differences["has_changes"],
            "summary": differences["summary"],
            "differences": differences["details"]
        }
    
    @staticmethod
    def _calculate_differences(
        old_data: List[Dict[str, Any]],
        new_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate differences between two data sets.
        
        Args:
            old_data: Older dataset
            new_data: Newer dataset
            
        Returns:
            Dictionary with difference details
        """
        # Convert lists to dictionaries keyed by identifier for easier comparison
        # Try common identifier fields
        identifier_fields = ['interface', 'name', 'network', 'destination', 'address', 'neighbor', 'mac_address']
        
        old_dict = {}
        new_dict = {}
        identifier_field = None
        
        # Find which identifier field to use
        for field in identifier_fields:
            if old_data and field in old_data[0]:
                identifier_field = field
                old_dict = {item[field]: item for item in old_data if field in item}
                new_dict = {item[field]: item for item in new_data if field in item}
                break
        
        if not identifier_field:
            # Fallback: use index as identifier
            old_dict = {i: item for i, item in enumerate(old_data)}
            new_dict = {i: item for i, item in enumerate(new_data)}
            identifier_field = "index"
        
        # Calculate differences
        old_keys = set(old_dict.keys())
        new_keys = set(new_dict.keys())
        
        added = new_keys - old_keys
        removed = old_keys - new_keys
        common = old_keys & new_keys
        
        # Check for changes in common items
        changed = []
        for key in common:
            old_item = old_dict[key]
            new_item = new_dict[key]
            
            # Compare all fields
            item_changes = {}
            all_fields = set(old_item.keys()) | set(new_item.keys())
            
            for field in all_fields:
                old_value = old_item.get(field)
                new_value = new_item.get(field)
                
                if old_value != new_value:
                    item_changes[field] = {
                        "old": old_value,
                        "new": new_value
                    }
            
            if item_changes:
                changed.append({
                    identifier_field: key,
                    "changes": item_changes
                })
        
        has_changes = bool(added or removed or changed)
        
        return {
            "has_changes": has_changes,
            "summary": {
                "items_added": len(added),
                "items_removed": len(removed),
                "items_changed": len(changed),
                "items_unchanged": len(common) - len(changed),
                "total_old": len(old_keys),
                "total_new": len(new_keys)
            },
            "details": {
                "added": [new_dict[key] for key in added],
                "removed": [old_dict[key] for key in removed],
                "changed": changed,
                "identifier_field": identifier_field
            }
        }


def format_comparison_report(comparison_result: Dict[str, Any]) -> str:
    """
    Format comparison results as a human-readable report.
    
    Args:
        comparison_result: Result from compare_baselines or compare_current_to_baseline
        
    Returns:
        Formatted text report
    """
    report_lines = []
    
    report_lines.append("=" * 80)
    report_lines.append("BASELINE COMPARISON REPORT")
    report_lines.append("=" * 80)
    report_lines.append("")
    
    # Header info
    report_lines.append(f"Device: {comparison_result.get('device_name', 'Unknown')} ({comparison_result.get('device_id')})")
    report_lines.append(f"Command: {comparison_result.get('command')}")
    report_lines.append("")
    
    # Baseline info
    if 'baseline_old' in comparison_result:
        report_lines.append(f"Comparing:")
        report_lines.append(f"  Old: Version {comparison_result['baseline_old']['version']} - {comparison_result['baseline_old']['updated_at']}")
        report_lines.append(f"  New: Version {comparison_result['baseline_new']['version']} - {comparison_result['baseline_new']['updated_at']}")
    else:
        report_lines.append(f"Baseline: Version {comparison_result['baseline']['version']} - {comparison_result['baseline']['updated_at']}")
        report_lines.append(f"Current: {comparison_result['current']['timestamp']}")
    
    report_lines.append("")
    
    # Summary
    summary = comparison_result['summary']
    report_lines.append("SUMMARY:")
    report_lines.append(f"  Changes Detected: {'YES' if comparison_result['has_changes'] else 'NO'}")
    report_lines.append(f"  Items Added: {summary['items_added']}")
    report_lines.append(f"  Items Removed: {summary['items_removed']}")
    report_lines.append(f"  Items Changed: {summary['items_changed']}")
    report_lines.append(f"  Items Unchanged: {summary['items_unchanged']}")
    report_lines.append("")
    
    # Details
    if comparison_result['has_changes']:
        report_lines.append("DETAILS:")
        report_lines.append("")
        
        details = comparison_result['differences']
        
        if details['added']:
            report_lines.append(f"  ADDED ({len(details['added'])}):")
            for item in details['added']:
                report_lines.append(f"    + {json.dumps(item, indent=6)}")
            report_lines.append("")
        
        if details['removed']:
            report_lines.append(f"  REMOVED ({len(details['removed'])}):")
            for item in details['removed']:
                report_lines.append(f"    - {json.dumps(item, indent=6)}")
            report_lines.append("")
        
        if details['changed']:
            report_lines.append(f"  CHANGED ({len(details['changed'])}):")
            for item in details['changed']:
                id_field = details['identifier_field']
                report_lines.append(f"    ~ {id_field}: {item[id_field]}")
                for field, change in item['changes'].items():
                    report_lines.append(f"      {field}:")
                    report_lines.append(f"        - Old: {change['old']}")
                    report_lines.append(f"        + New: {change['new']}")
            report_lines.append("")
    
    report_lines.append("=" * 80)
    
    return "\n".join(report_lines)
