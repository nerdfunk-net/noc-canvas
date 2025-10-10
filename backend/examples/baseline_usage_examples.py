"""
Example usage of the baseline feature.

This script demonstrates how to:
1. Create baselines for devices
2. Compare baseline versions
3. Compare current state to baseline
4. Generate comparison reports
"""

import json
from datetime import datetime

from app.core.database import SessionLocal
from app.models.device_cache import BaselineCache
from app.services.baseline_comparison import (
    BaselineComparator,
    format_comparison_report,
)
from app.services.background_jobs import celery_app, CELERY_AVAILABLE


def example_1_create_baseline():
    """
    Example 1: Create a baseline for specific devices.
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 1: Create Baseline")
    print("=" * 60)

    if not CELERY_AVAILABLE:
        print("❌ Celery is not available. Cannot run this example.")
        return

    # Baseline specific devices
    device_ids = [
        "device-uuid-1",
        "device-uuid-2",
    ]

    print(f"\n📊 Creating baseline for {len(device_ids)} devices...")

    result = celery_app.send_task(
        "app.tasks.baseline_tasks.create_baseline",
        kwargs={
            "device_ids": device_ids,
            "notes": f"Example baseline created at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "auth_token": "your-auth-token-here",
        },
    )

    print(f"✅ Task submitted with ID: {result.id}")
    print(f"   Monitor progress at: /api/jobs/{result.id}")


def example_2_create_baseline_all_devices():
    """
    Example 2: Create baseline for ALL devices.
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Create Baseline for All Devices")
    print("=" * 60)

    if not CELERY_AVAILABLE:
        print("❌ Celery is not available. Cannot run this example.")
        return

    print("\n📊 Creating baseline for ALL devices in Nautobot...")

    result = celery_app.send_task(
        "app.tasks.baseline_tasks.create_baseline",
        kwargs={
            "notes": "Automated weekly baseline",
            "auth_token": "your-auth-token-here",
        },
    )

    print(f"✅ Task submitted with ID: {result.id}")


def example_3_create_routing_baseline():
    """
    Example 3: Create baseline for specific commands only (routing).
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Create Routing-Only Baseline")
    print("=" * 60)

    if not CELERY_AVAILABLE:
        print("❌ Celery is not available. Cannot run this example.")
        return

    routing_commands = [
        "show ip route static",
        "show ip route ospf",
        "show ip route bgp",
    ]

    print(f"\n📊 Creating routing baseline (commands: {routing_commands})...")

    result = celery_app.send_task(
        "app.tasks.baseline_tasks.create_baseline",
        kwargs={
            "commands": routing_commands,
            "notes": "Pre-BGP-migration routing baseline",
            "auth_token": "your-auth-token-here",
        },
    )

    print(f"✅ Task submitted with ID: {result.id}")


def example_4_compare_baseline_versions():
    """
    Example 4: Compare two baseline versions for a device.
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Compare Baseline Versions")
    print("=" * 60)

    db = SessionLocal()

    try:
        # Example parameters (replace with actual values)
        device_id = "your-device-uuid"
        command = "show interfaces"

        # Get baseline history
        history = BaselineComparator.get_baseline_history(
            db, device_id, command, limit=5
        )

        if len(history) < 2:
            print(
                f"❌ Need at least 2 baseline versions to compare. Found: {len(history)}"
            )
            return

        print(f"\n📊 Found {len(history)} baseline versions for device {device_id}")
        print(f"   Command: {command}")
        print("\nVersions:")
        for baseline in history:
            print(
                f"   - Version {baseline.baseline_version}: {baseline.updated_at} - {baseline.notes}"
            )

        # Compare latest two versions
        baseline_new = history[0]  # Most recent
        baseline_old = history[1]  # Previous

        print(
            f"\n🔍 Comparing version {baseline_old.baseline_version} → {baseline_new.baseline_version}"
        )

        comparison = BaselineComparator.compare_baselines(
            baseline_old, baseline_new, use_normalized=True
        )

        # Generate and print report
        report = format_comparison_report(comparison)
        print(report)

        # Also show as JSON
        print("\nJSON Result:")
        print(json.dumps(comparison, indent=2))

    finally:
        db.close()


def example_5_compare_current_to_baseline():
    """
    Example 5: Compare current device state to baseline.
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Compare Current State to Baseline")
    print("=" * 60)

    db = SessionLocal()

    try:
        # Example: Simulate current device output
        # In production, you'd execute the command on the device
        current_output = [
            {
                "interface": "GigabitEthernet0/1",
                "status": "up",
                "protocol": "up",
                "description": "Uplink to Core",
            },
            {
                "interface": "GigabitEthernet0/2",
                "status": "down",  # This changed!
                "protocol": "down",
                "description": "Backup Link",
            },
        ]

        device_id = "your-device-uuid"
        command = "show interfaces"

        print(f"\n🔍 Comparing current state to baseline for device {device_id}")
        print(f"   Command: {command}")

        comparison = BaselineComparator.compare_current_to_baseline(
            db, device_id, command, current_output, use_normalized=True
        )

        if "error" in comparison:
            print(f"❌ Error: {comparison['error']}")
            return

        # Generate report
        report = format_comparison_report(comparison)
        print(report)

        # Alert if changes detected
        if comparison["has_changes"]:
            print("\n⚠️  ALERT: Configuration drift detected!")
            print(f"   {comparison['summary']['items_changed']} items changed")
            print(f"   {comparison['summary']['items_added']} items added")
            print(f"   {comparison['summary']['items_removed']} items removed")
        else:
            print("\n✅ No configuration drift detected.")

    finally:
        db.close()


def example_6_query_baselines():
    """
    Example 6: Query and inspect baseline data.
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 6: Query Baseline Data")
    print("=" * 60)

    db = SessionLocal()

    try:
        # Get all baselines for a device
        device_id = "your-device-uuid"

        baselines = (
            db.query(BaselineCache).filter(BaselineCache.device_id == device_id).all()
        )

        print(f"\n📊 Found {len(baselines)} baseline records for device {device_id}")

        # Group by command
        by_command = {}
        for baseline in baselines:
            if baseline.command not in by_command:
                by_command[baseline.command] = []
            by_command[baseline.command].append(baseline)

        print("\nBaselines by command:")
        for command, command_baselines in by_command.items():
            print(f"\n  {command} ({len(command_baselines)} versions):")
            for baseline in sorted(command_baselines, key=lambda x: x.baseline_version):
                print(
                    f"    - Version {baseline.baseline_version}: {baseline.updated_at}"
                )
                print(f"      Notes: {baseline.notes}")

                # Show size of data
                raw_size = len(baseline.raw_output)
                normalized_size = (
                    len(baseline.normalized_output) if baseline.normalized_output else 0
                )
                print(
                    f"      Data size: {raw_size:,} bytes (raw), {normalized_size:,} bytes (normalized)"
                )

        # Show sample data
        if baselines:
            print("\n📄 Sample baseline data:")
            sample = baselines[0]
            print(f"   Command: {sample.command}")
            print(f"   Device: {sample.device_name}")

            # Parse and show first few entries
            data = json.loads(sample.normalized_output or sample.raw_output)
            if data:
                print(f"   Entries: {len(data)}")
                print("   Sample entry:")
                print(json.dumps(data[0], indent=6))

    finally:
        db.close()


def example_7_scheduled_baseline():
    """
    Example 7: Create a scheduled baseline task.
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 7: Create Scheduled Baseline Task")
    print("=" * 60)

    print("""
To create a scheduled baseline task via the UI:

1. Navigate to the Scheduler tab
2. Click "Create New Task"
3. Fill in the form:
   
   Name: Weekly Device Baseline
   Task: app.tasks.baseline_tasks.create_baseline
   
   Schedule Type: Crontab
   - Minute: 0
   - Hour: 2
   - Day of Week: 0 (Sunday)
   - Day of Month: *
   - Month: *
   
   Task Arguments (JSON):
   {
     "notes": "Automated weekly baseline"
   }
   
4. Click "Create Task"

This will baseline all devices every Sunday at 2:00 AM.

For specific devices:
   Task Arguments (JSON):
   {
     "device_ids": ["uuid1", "uuid2", "uuid3"],
     "notes": "Critical devices weekly baseline"
   }

For specific commands only:
   Task Arguments (JSON):
   {
     "commands": ["show ip route static", "show ip route ospf"],
     "notes": "Routing baseline"
   }
""")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("BASELINE FEATURE EXAMPLES")
    print("=" * 80)

    print("""
This script demonstrates various baseline feature capabilities.
Update the device_id and auth_token values before running examples.

Available examples:
  1. Create baseline for specific devices
  2. Create baseline for ALL devices
  3. Create baseline for specific commands (routing only)
  4. Compare two baseline versions
  5. Compare current state to baseline
  6. Query and inspect baseline data
  7. Create scheduled baseline task (instructions)
""")

    # Uncomment the examples you want to run:

    # example_1_create_baseline()
    # example_2_create_baseline_all_devices()
    # example_3_create_routing_baseline()
    # example_4_compare_baseline_versions()
    # example_5_compare_current_to_baseline()
    # example_6_query_baselines()
    example_7_scheduled_baseline()

    print("\n" + "=" * 80)
    print("Examples complete!")
    print("=" * 80)
