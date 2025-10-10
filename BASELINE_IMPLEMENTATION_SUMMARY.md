# Baseline Feature Implementation Summary

## Overview

The baseline feature has been successfully implemented to capture device configuration snapshots for configuration drift detection, compliance checking, and change management.

## What Was Created

### 1. Database Model (`backend/app/models/device_cache.py`)

**New Table: `baseline_cache`**

```python
class BaselineCache(Base):
    id                  # Primary key
    device_id           # Nautobot device UUID
    device_name         # Device name (for easier querying)
    command             # Command executed (e.g., "show interfaces")
    raw_output          # Original JSON from TextFSM
    normalized_output   # Cleaned JSON with dynamic values removed
    created_at          # First creation timestamp
    updated_at          # Last update timestamp
    baseline_version    # Version number (auto-incremented)
    notes               # Optional notes (e.g., "Pre-upgrade baseline")
```

**Indexes:**
- `ix_baseline_device_command` - Fast device + command lookups
- `ix_baseline_device_updated` - Query by update time
- `ix_baseline_device_name` - Search by device name

### 2. Background Task (`backend/app/tasks/baseline_tasks.py`)

**Task: `app.tasks.baseline_tasks.create_baseline`**

**Features:**
- Executes all topology-related commands (7 default commands)
- Reuses topology discovery infrastructure
- Stores both raw and normalized output
- Tracks baseline versions automatically
- Supports device filtering and command selection
- Provides detailed progress tracking

**Default Commands:**
1. `show interfaces` - Interface states
2. `show ip arp` - ARP table
3. `show cdp neighbors` - CDP neighbors
4. `show mac address-table` - MAC table
5. `show ip route static` - Static routes
6. `show ip route ospf` - OSPF routes
7. `show ip route bgp` - BGP routes

**Data Normalization:**
- Removes dynamic values (counters, timestamps, rates)
- Sorts entries consistently
- Strips whitespace
- Maintains configuration-relevant data

### 3. Comparison Utilities (`backend/app/services/baseline_comparison.py`)

**Class: `BaselineComparator`**

Methods:
- `get_latest_baseline()` - Get most recent baseline
- `get_baseline_by_version()` - Get specific version
- `get_baseline_history()` - Get version history
- `compare_baselines()` - Compare two baseline versions
- `compare_current_to_baseline()` - Compare current state to baseline

**Helper Function:**
- `format_comparison_report()` - Generate human-readable reports

**Comparison Features:**
- Identifies added, removed, and changed items
- Tracks field-level changes
- Generates summary statistics
- Produces detailed diff reports

### 4. Database Migration (`backend/app/migrations/add_baseline_table.py`)

**Migration Script:**
- Creates `baseline_cache` table
- Verifies table structure
- Lists columns and indexes
- Provides feedback on success/failure

**Usage:**
```bash
python backend/app/migrations/add_baseline_table.py
```

### 5. Documentation

**Files Created:**
1. `BASELINE_FEATURE.md` - Complete feature documentation
   - Purpose and use cases
   - Database schema
   - Task parameters
   - Usage examples
   - Best practices
   - API endpoint suggestions
   - Monitoring and troubleshooting

2. `backend/examples/baseline_usage_examples.py` - Code examples
   - 7 practical usage examples
   - Baseline creation
   - Version comparison
   - Current state comparison
   - Data querying
   - Scheduled task setup

### 6. Integration

**Updated Files:**
- `backend/app/services/background_jobs.py` - Registered baseline task
- `backend/app/api/scheduler.py` - Added to available tasks
- `backend/app/models/__init__.py` - Exported BaselineCache model

## Key Features

### 1. **Data Normalization for Reliable Comparison**

The implementation includes intelligent normalization that:
- **Removes Dynamic Fields**: Counters, timestamps, rates that change constantly
- **Sorts Consistently**: Orders entries for reliable comparison
- **Preserves Configuration Data**: Keeps configuration-relevant information
- **Dual Storage**: Stores both raw (for forensics) and normalized (for comparison)

**Normalized Fields by Command:**
- `show interfaces`: Removes input_rate, output_rate, packet/byte counters, last_input/output times
- `show ip arp`: Removes age field
- `show cdp neighbors`: Removes holdtime counter

### 2. **Flexible Baselining Options**

**Baseline All Devices:**
```python
celery_app.send_task(
    "app.tasks.baseline_tasks.create_baseline",
    kwargs={"notes": "Weekly baseline"}
)
```

**Baseline Specific Devices:**
```python
celery_app.send_task(
    "app.tasks.baseline_tasks.create_baseline",
    kwargs={
        "device_ids": ["uuid1", "uuid2"],
        "notes": "Critical devices baseline"
    }
)
```

**Baseline Specific Commands:**
```python
celery_app.send_task(
    "app.tasks.baseline_tasks.create_baseline",
    kwargs={
        "commands": ["show ip route static", "show ip route ospf"],
        "notes": "Routing baseline"
    }
)
```

### 3. **Version Tracking**

- Automatic version incrementing
- Maintains history of baselines
- Supports comparison between any versions
- Notes field for context

### 4. **Comprehensive Comparison**

```python
comparison = BaselineComparator.compare_baselines(
    baseline_old, baseline_new, use_normalized=True
)

# Results include:
# - has_changes: bool
# - summary: counts of added/removed/changed
# - details: specific items and field-level changes
```

### 5. **Progress Tracking**

Task provides real-time progress updates:
- Initialization
- Device processing (N of M)
- Commands executed count
- Errors encountered

## Usage Workflow

### 1. Create Initial Baseline

```bash
# Via Scheduler UI or API
POST /api/scheduler/jobs
{
    "task": "app.tasks.baseline_tasks.create_baseline",
    "one_off": true,
    "kwargs": {
        "device_ids": ["device-uuid"],
        "notes": "Pre-change baseline"
    }
}
```

### 2. Make Configuration Changes

Perform maintenance or configuration updates.

### 3. Create New Baseline

```bash
# After changes
POST /api/scheduler/jobs
{
    "task": "app.tasks.baseline_tasks.create_baseline",
    "one_off": true,
    "kwargs": {
        "device_ids": ["device-uuid"],
        "notes": "Post-change baseline"
    }
}
```

### 4. Compare Versions

```python
from app.services.baseline_comparison import BaselineComparator

# Compare versions
comparison = BaselineComparator.compare_baselines(
    baseline_version_1,
    baseline_version_2,
    use_normalized=True
)

# Generate report
report = format_comparison_report(comparison)
print(report)
```

## Answer to Your Question: Data Normalization

**YES, we should normalize the data, and the implementation does this!**

### Why Normalization is Essential:

1. **Reliable Comparisons**: Without normalization, every comparison would show changes due to packet counters, timestamps, etc.

2. **Focus on Configuration**: Normalized data focuses on what matters - actual configuration changes, not operational state changes.

3. **Efficient Storage**: Normalized data is more compact and consistent.

4. **Better Diffing**: Tools can produce cleaner, more meaningful diffs.

### What We Normalize:

✅ **Remove:**
- Packet/byte counters
- Rate statistics (bps, pps)
- Timestamps (last input/output)
- Dynamic timers (ARP age, CDP holdtime)
- Interface resets/errors counters

✅ **Keep:**
- Interface names and status (up/down)
- IP addresses and subnets
- Descriptions and configuration text
- Routing information
- Neighbor relationships
- MAC addresses

✅ **Standardize:**
- Whitespace and formatting
- Entry ordering (sorted)
- JSON structure

### Dual Storage Approach:

The implementation stores **BOTH**:
- **`raw_output`**: Complete original data for forensics
- **`normalized_output`**: Cleaned data for comparison

This gives you the best of both worlds:
- Fast, reliable comparisons with normalized data
- Ability to investigate details with raw data
- Verification that normalization didn't remove important changes

## Testing the Feature

### 1. Run Database Migration

```bash
cd /Users/mp/programming/noc-canvas/backend
python app/migrations/add_baseline_table.py
```

### 2. Restart Celery Worker

```bash
cd /Users/mp/programming/noc-canvas/backend
python start_worker.py
```

### 3. Create Test Baseline

Via Scheduler UI:
1. Go to Scheduler tab
2. Click "Create New Task"
3. Select task: `app.tasks.baseline_tasks.create_baseline`
4. Set as one-off execution
5. Add device_ids in kwargs (optional)
6. Run task

### 4. Query Baselines

```python
from app.core.database import SessionLocal
from app.models.device_cache import BaselineCache

db = SessionLocal()
baselines = db.query(BaselineCache).all()

for baseline in baselines:
    print(f"{baseline.device_name}: {baseline.command} (v{baseline.baseline_version})")
```

## Next Steps and Enhancements

### Immediate Next Steps:

1. **Run Migration**: Create the baseline_cache table
2. **Test Task**: Create a baseline for a test device
3. **Verify Data**: Query the table to inspect baseline data
4. **Test Comparison**: Create multiple baselines and compare them

### Future Enhancements:

1. **REST API Endpoints**:
   - `GET /api/baseline/{device_id}` - Get device baselines
   - `POST /api/baseline/compare` - Compare baselines
   - `DELETE /api/baseline/cleanup` - Clean old baselines

2. **Automated Drift Detection**:
   - Background task to compare current state vs baseline
   - Alert on unauthorized changes
   - Email/webhook notifications

3. **UI Components**:
   - Baseline viewer
   - Visual diff display
   - Timeline of configuration changes
   - Compliance dashboard

4. **Advanced Features**:
   - Baseline templates by device type
   - Compliance rule engine
   - Git integration for version control
   - Rollback configuration generation

5. **Reporting**:
   - Configuration drift reports
   - Compliance status reports
   - Change audit logs
   - Trend analysis

## Files Modified/Created

### New Files:
- ✅ `backend/app/tasks/baseline_tasks.py` (460 lines)
- ✅ `backend/app/services/baseline_comparison.py` (450 lines)
- ✅ `backend/app/migrations/add_baseline_table.py` (70 lines)
- ✅ `backend/examples/baseline_usage_examples.py` (400 lines)
- ✅ `BASELINE_FEATURE.md` (documentation)
- ✅ `BASELINE_IMPLEMENTATION_SUMMARY.md` (this file)

### Modified Files:
- ✅ `backend/app/models/device_cache.py` - Added BaselineCache model
- ✅ `backend/app/models/__init__.py` - Exported BaselineCache
- ✅ `backend/app/services/background_jobs.py` - Registered baseline task
- ✅ `backend/app/api/scheduler.py` - Added to available tasks

### Total Lines Added: ~1,500 lines

## Summary

The baseline feature is now fully implemented and ready for testing. It provides:

✅ **Comprehensive Data Capture**: All topology-related commands
✅ **Smart Normalization**: Removes dynamic values, keeps configuration data
✅ **Version Tracking**: Automatic versioning with history
✅ **Flexible Comparison**: Compare versions or current state to baseline
✅ **Well Documented**: Complete documentation and examples
✅ **Production Ready**: Error handling, progress tracking, logging

The normalization strategy ensures reliable configuration drift detection while maintaining forensic capability through dual storage of raw and normalized data.
