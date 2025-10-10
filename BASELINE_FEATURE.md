# Baseline Configuration Snapshot Feature

## Overview

The baseline feature captures device configuration snapshots for configuration drift detection, compliance checking, and change management. It executes all topology-related commands on network devices and stores both raw and normalized output for future comparison.

## Purpose

- **Configuration Drift Detection**: Compare current device state against known good baseline
- **Change Management**: Track what changed between maintenance windows
- **Compliance Checking**: Verify devices maintain required configurations
- **Troubleshooting**: Identify when and what configuration changes occurred
- **Rollback Reference**: Understand pre-change state for rollback decisions

## Database Schema

### BaselineCache Table

The `baseline_cache` table stores device configuration snapshots:

```python
class BaselineCache(Base):
    id                  # Primary key
    device_id           # Nautobot device UUID
    device_name         # Device name (indexed for easy querying)
    command             # Command executed (e.g., "show interfaces")
    raw_output          # Original JSON from TextFSM parser
    normalized_output   # Cleaned JSON with dynamic values removed
    created_at          # When baseline was first created
    updated_at          # Last update timestamp
    baseline_version    # Version number (incremented on updates)
    notes               # Optional notes (e.g., "Pre-upgrade baseline")
```

### Indexes

- `ix_baseline_device_command`: Fast lookup by device + command
- `ix_baseline_device_updated`: Query baselines by update time
- `ix_baseline_device_name`: Search by device name

## Background Task

### Task Name
`app.tasks.baseline_tasks.create_baseline`

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `device_ids` | List[str] | No | List of device IDs to baseline. If omitted, baselines ALL devices |
| `commands` | List[str] | No | Specific commands to execute. If omitted, runs all default commands |
| `notes` | str | No | Notes about this baseline (e.g., "Pre-upgrade baseline 2025-10-10") |
| `auth_token` | str | Yes | Authentication token for device access |

### Default Commands

The task executes these commands by default:

1. **`show interfaces`** - Interface states and configuration
2. **`show ip arp`** - ARP table entries
3. **`show cdp neighbors`** - CDP neighbor information
4. **`show mac address-table`** - MAC address table
5. **`show ip route static`** - Static routes
6. **`show ip route ospf`** - OSPF routes
7. **`show ip route bgp`** - BGP routes

### Return Value

```json
{
    "status": "completed",
    "devices_processed": 15,
    "total_devices": 20,
    "total_commands": 105,
    "baseline_ids": [1, 2, 3, ...],
    "errors": [
        {
            "device_id": "uuid",
            "device_name": "router1",
            "command": "show interfaces",
            "error": "Connection timeout"
        }
    ],
    "message": "Successfully created/updated baselines for 15/20 devices (105 total commands)"
}
```

## Data Normalization

### Why Normalize?

Raw command output contains many dynamic values that change constantly but don't indicate configuration changes:

- **Counters**: Packet counts, byte counts, errors
- **Timestamps**: Last input/output times, uptime
- **Dynamic Status**: Rate statistics, queue depths
- **Timers**: CDP holdtimes, ARP age

### Normalization Process

The `_normalize_output()` function:

1. **Removes Dynamic Fields** based on command type:
   - `show interfaces`: Removes rates, counters, last I/O times
   - `show ip arp`: Removes age field
   - `show cdp neighbors`: Removes holdtime counter

2. **Normalizes Formatting**:
   - Strips whitespace
   - Sorts entries consistently
   - Standardizes JSON structure

3. **Maintains Structure**:
   - Keeps configuration-relevant data
   - Preserves relationships between entries
   - Retains identifiers for correlation

### Storage Strategy

Both versions are stored:

- **`raw_output`**: Complete original data for forensic analysis
- **`normalized_output`**: Cleaned data for efficient comparison

This dual approach allows:
- Fast comparison using normalized data
- Detailed investigation using raw data
- Verification that normalization didn't remove important changes

## Usage Examples

### 1. Baseline All Devices (Scheduled Task)

Create a scheduled task in the UI to baseline all devices weekly:

```json
{
    "task": "app.tasks.baseline_tasks.create_baseline",
    "name": "Weekly Baseline",
    "schedule": {
        "crontab": {
            "minute": "0",
            "hour": "2",
            "day_of_week": "0"
        }
    },
    "kwargs": {
        "notes": "Weekly automated baseline"
    }
}
```

### 2. Baseline Specific Devices

Before maintenance, baseline critical devices:

```python
# Via API or direct task submission
celery_app.send_task(
    "app.tasks.baseline_tasks.create_baseline",
    kwargs={
        "device_ids": ["uuid1", "uuid2", "uuid3"],
        "notes": "Pre-upgrade baseline 2025-10-10",
        "auth_token": user_token
    }
)
```

### 3. Baseline Specific Commands Only

Capture only routing information:

```python
celery_app.send_task(
    "app.tasks.baseline_tasks.create_baseline",
    kwargs={
        "commands": [
            "show ip route static",
            "show ip route ospf",
            "show ip route bgp"
        ],
        "notes": "Routing baseline before BGP changes",
        "auth_token": user_token
    }
)
```

## Comparison Workflow

### Step 1: Create Initial Baseline

```bash
# Before making changes
curl -X POST /api/scheduler/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "task": "app.tasks.baseline_tasks.create_baseline",
    "one_off": true,
    "kwargs": {
      "device_ids": ["device-uuid"],
      "notes": "Pre-change baseline"
    }
  }'
```

### Step 2: Make Configuration Changes

Perform your maintenance or configuration updates.

### Step 3: Query Baseline Data

```python
from app.models.device_cache import BaselineCache
from sqlalchemy import and_

# Get baseline for device and command
baseline = db.query(BaselineCache).filter(
    and_(
        BaselineCache.device_id == "device-uuid",
        BaselineCache.command == "show interfaces"
    )
).first()

# Parse normalized output for comparison
import json
baseline_data = json.loads(baseline.normalized_output)
```

### Step 4: Compare Current State

```python
# Execute command on device now
current_data = execute_command(device, "show interfaces")

# Compare with baseline
differences = compare_configs(baseline_data, current_data)

# Example diff output
{
    "added_interfaces": ["GigabitEthernet0/5"],
    "removed_interfaces": [],
    "changed_interfaces": [
        {
            "interface": "GigabitEthernet0/1",
            "changes": {
                "status": {"old": "up", "new": "down"},
                "description": {"old": "Uplink", "new": "Unused"}
            }
        }
    ]
}
```

## Best Practices

### 1. Baseline Frequency

- **Production Devices**: Weekly or bi-weekly
- **Critical Devices**: Before/after every change window
- **Development Devices**: Monthly or as needed

### 2. Baseline Timing

- Run during maintenance windows when possible
- Avoid peak hours to reduce device load
- Schedule at consistent times for trend analysis

### 3. Storage Management

- Keep at least 3-4 historical baselines per device
- Archive old baselines (>6 months) to separate storage
- Implement cleanup task for baselines older than 1 year

### 4. Versioning Strategy

- Use descriptive notes: "Pre-IOS-upgrade", "Post-BGP-config"
- Increment `baseline_version` on updates (automatic)
- Tag major changes: "v1.0-production", "v2.0-post-migration"

### 5. Comparison Logic

```python
def compare_baselines(old_baseline, new_baseline):
    """
    Compare two baseline versions.
    Returns structured diff showing changes.
    """
    old_data = json.loads(old_baseline.normalized_output)
    new_data = json.loads(new_baseline.normalized_output)
    
    # Use library like deepdiff for complex comparisons
    from deepdiff import DeepDiff
    
    diff = DeepDiff(old_data, new_data, ignore_order=True)
    
    return {
        "baseline_old": {
            "version": old_baseline.baseline_version,
            "date": old_baseline.updated_at,
            "notes": old_baseline.notes
        },
        "baseline_new": {
            "version": new_baseline.baseline_version,
            "date": new_baseline.updated_at,
            "notes": new_baseline.notes
        },
        "differences": diff,
        "summary": {
            "items_added": len(diff.get('iterable_item_added', {})),
            "items_removed": len(diff.get('iterable_item_removed', {})),
            "values_changed": len(diff.get('values_changed', {}))
        }
    }
```

## API Endpoints (Future Enhancement)

Consider adding these REST endpoints:

### Get Device Baselines
```
GET /api/baseline/{device_id}
Query params: ?command=show%20interfaces&limit=5
```

### Compare Baselines
```
POST /api/baseline/compare
Body: {
    "device_id": "uuid",
    "command": "show interfaces",
    "baseline_version_old": 1,
    "baseline_version_new": 2
}
```

### Delete Old Baselines
```
DELETE /api/baseline/cleanup
Query params: ?older_than_days=180
```

## Monitoring and Alerts

### Baseline Creation Monitoring

Monitor task execution:
- Success rate per device
- Commands failing consistently
- Execution time trends
- Storage growth rate

### Drift Detection

Set up alerts for significant changes:
- Interface status changes (up/down)
- New/removed CDP neighbors
- Route table modifications
- ACL or security policy changes

## Troubleshooting

### Common Issues

**1. "Device not found in Nautobot"**
- Verify device exists in Nautobot
- Check device ID is correct UUID
- Ensure device has primary IPv4 address

**2. "Platform/network_driver not configured"**
- Device must have platform assigned in Nautobot
- Platform must have `network_driver` field set
- Supported drivers: cisco_ios, cisco_nxos, arista_eos, etc.

**3. "Command execution failed"**
- Check device connectivity
- Verify SSH credentials are configured
- Ensure device supports the command
- Check TextFSM templates exist for command

**4. "No structured data returned"**
- Command output may not be parseable by TextFSM
- Check if template exists for device platform
- Review raw output in error logs

### Performance Optimization

- Use `device_ids` parameter to limit scope
- Schedule during off-peak hours
- Consider parallelization for large deployments
- Monitor task queue depth

## Security Considerations

1. **Sensitive Data**: Baselines may contain sensitive information (IP addresses, network topology)
2. **Access Control**: Implement RBAC for baseline viewing
3. **Data Retention**: Define and enforce retention policies
4. **Encryption**: Consider encrypting baseline data at rest
5. **Audit Logging**: Log all baseline access and modifications

## Future Enhancements

1. **Automatic Drift Detection**: Background task to compare current state vs baseline
2. **Change Notifications**: Alert on unauthorized configuration changes
3. **Compliance Reports**: Generate compliance status reports
4. **Baseline Templates**: Pre-defined baseline profiles for device types
5. **Rollback Assistance**: Use baselines to generate rollback configurations
6. **Trend Analysis**: Identify configuration drift patterns over time
7. **Integration**: Export baselines to Git for version control
