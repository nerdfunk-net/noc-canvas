# Baseline Feature Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Run Database Migration (1 minute)

```bash
cd /Users/mp/programming/noc-canvas/backend
python app/migrations/add_baseline_table.py
```

Expected output:
```
============================================================
Baseline Table Migration
============================================================

📊 Creating 'baseline_cache' table...
✅ Successfully created 'baseline_cache' table

📋 Table structure:
   Columns: 9
      - id: INTEGER
      - device_id: VARCHAR
      - device_name: VARCHAR
      - command: VARCHAR
      - raw_output: TEXT
      - normalized_output: TEXT
      - created_at: DATETIME
      - updated_at: DATETIME
      - baseline_version: INTEGER
      - notes: VARCHAR

🔍 Indexes: 3
      - ix_baseline_device_command: ['device_id', 'command']
      - ix_baseline_device_updated: ['device_id', 'updated_at']
      - ix_baseline_device_name: ['device_name']

============================================================
Migration completed successfully!
============================================================
```

### Step 2: Restart Celery Worker (1 minute)

```bash
# Stop existing worker (Ctrl+C if running)

# Start worker with new baseline task
cd /Users/mp/programming/noc-canvas/backend
python start_worker.py
```

Look for this in the worker output:
```
[tasks]
  . app.tasks.baseline_tasks.create_baseline
  . app.tasks.cache_tasks.cache_warm_up
  . app.tasks.checkmk_tasks.bulk_host_operations
  . app.tasks.checkmk_tasks.sync_checkmk_hosts
  ...
```

### Step 3: Create Your First Baseline (2 minutes)

#### Option A: Via Scheduler UI

1. Navigate to **Scheduler** tab
2. Click **"Create New Task"**
3. Fill in the form:
   - **Name**: `My First Baseline`
   - **Task**: `app.tasks.baseline_tasks.create_baseline`
   - **Execute Now**: ☑️ (checked)
   - **Enabled**: ☑️ (checked)
   
4. **Task Arguments** (JSON):
   ```json
   {
     "notes": "My first baseline test"
   }
   ```
   
5. Click **"Create Task"**
6. Go to **Jobs** tab to monitor progress

#### Option B: Via Python Script

```python
from app.services.background_jobs import celery_app

# Submit baseline task
result = celery_app.send_task(
    "app.tasks.baseline_tasks.create_baseline",
    kwargs={
        "notes": "My first baseline test",
        "auth_token": "your-token-here"
    }
)

print(f"Task ID: {result.id}")
```

### Step 4: Check Results (1 minute)

```python
from app.core.database import SessionLocal
from app.models.device_cache import BaselineCache

db = SessionLocal()

# Count baselines created
count = db.query(BaselineCache).count()
print(f"Total baselines: {count}")

# Show recent baselines
baselines = db.query(BaselineCache).order_by(
    BaselineCache.created_at.desc()
).limit(5).all()

for baseline in baselines:
    print(f"Device: {baseline.device_name}")
    print(f"  Command: {baseline.command}")
    print(f"  Version: {baseline.baseline_version}")
    print(f"  Updated: {baseline.updated_at}")
    print(f"  Notes: {baseline.notes}")
    print()

db.close()
```

## 📊 Common Use Cases

### Use Case 1: Baseline Before Maintenance

**Scenario**: You need to upgrade device firmware and want to capture pre-upgrade state.

```json
{
  "task": "app.tasks.baseline_tasks.create_baseline",
  "name": "Pre-Upgrade Baseline",
  "one_off": true,
  "kwargs": {
    "device_ids": ["critical-router-uuid", "critical-switch-uuid"],
    "notes": "Pre-firmware-upgrade baseline - 2025-10-10"
  }
}
```

After maintenance, create post-upgrade baseline:
```json
{
  "notes": "Post-firmware-upgrade baseline - 2025-10-10"
}
```

Then compare the two versions!

### Use Case 2: Weekly Automated Baseline

**Scenario**: Automatically baseline all devices every Sunday at 2 AM.

```json
{
  "task": "app.tasks.baseline_tasks.create_baseline",
  "name": "Weekly Full Baseline",
  "enabled": true,
  "crontab": {
    "minute": "0",
    "hour": "2",
    "day_of_week": "0",
    "day_of_month": "*",
    "month_of_year": "*"
  },
  "kwargs": {
    "notes": "Automated weekly baseline"
  }
}
```

### Use Case 3: Routing Changes Only

**Scenario**: You're making BGP changes and only want to baseline routing.

```json
{
  "task": "app.tasks.baseline_tasks.create_baseline",
  "name": "Routing Baseline",
  "one_off": true,
  "kwargs": {
    "commands": [
      "show ip route static",
      "show ip route ospf",
      "show ip route bgp"
    ],
    "notes": "Pre-BGP-migration routing baseline"
  }
}
```

## 🔍 Comparing Baselines

### Simple Comparison Script

Save as `compare_baseline.py`:

```python
from app.core.database import SessionLocal
from app.services.baseline_comparison import BaselineComparator, format_comparison_report

# Configuration
DEVICE_ID = "your-device-uuid-here"
COMMAND = "show interfaces"

db = SessionLocal()

try:
    # Get baseline history
    history = BaselineComparator.get_baseline_history(
        db, DEVICE_ID, COMMAND, limit=5
    )
    
    if len(history) < 2:
        print(f"Need at least 2 baselines. Found: {len(history)}")
        exit(1)
    
    print(f"Found {len(history)} baseline versions\n")
    
    # Compare latest two
    baseline_new = history[0]
    baseline_old = history[1]
    
    print(f"Comparing:")
    print(f"  Old: v{baseline_old.baseline_version} - {baseline_old.updated_at}")
    print(f"  New: v{baseline_new.baseline_version} - {baseline_new.updated_at}")
    print()
    
    # Compare
    comparison = BaselineComparator.compare_baselines(
        baseline_old, baseline_new, use_normalized=True
    )
    
    # Print report
    report = format_comparison_report(comparison)
    print(report)
    
    # Alert if changes detected
    if comparison['has_changes']:
        print("\n⚠️  CONFIGURATION DRIFT DETECTED!")
    else:
        print("\n✅ No configuration changes detected")
        
finally:
    db.close()
```

Run it:
```bash
cd /Users/mp/programming/noc-canvas/backend
python compare_baseline.py
```

## 📅 Recommended Schedule

### For Production Devices:
- **Weekly Baseline**: Every Sunday 2 AM
  - All commands
  - All devices
  - Notes: "Weekly automated baseline"

### For Critical Devices:
- **Daily Baseline**: Every day 2 AM
  - Interface and routing commands only
  - Critical device list
  - Notes: "Daily critical device baseline"

### Before Changes:
- **On-Demand Baseline**: Before any maintenance
  - Specific devices being changed
  - All commands
  - Notes: "Pre-[change-type] baseline - [date]"

### After Changes:
- **On-Demand Baseline**: After maintenance completes
  - Same devices as pre-change
  - All commands
  - Notes: "Post-[change-type] baseline - [date]"

## 🛠️ Troubleshooting

### Problem: "No baselines found"

**Solution**: Check task execution
```python
from app.services.background_jobs import background_job_service

# Get task status
status = background_job_service.get_job_status("task-id-here")
print(status)
```

### Problem: "Task failed with connection error"

**Possible causes:**
1. Device unreachable
2. SSH credentials not configured
3. Device platform/network_driver not set

**Solution**: Check device connectivity
```bash
# Test SSH manually
ssh username@device-ip

# Check device in Nautobot has:
# - Primary IPv4 address
# - Platform with network_driver
```

### Problem: "Command returned no data"

**Possible causes:**
1. TextFSM template missing for command
2. Device output format different
3. Command not supported on device

**Solution**: Check raw output in logs
```python
# View raw output
baseline = db.query(BaselineCache).filter(
    BaselineCache.device_id == "device-uuid"
).first()

import json
raw_data = json.loads(baseline.raw_output)
print(json.dumps(raw_data, indent=2))
```

## 📚 Next Steps

1. **Set up automated baselines**: Create weekly scheduled task
2. **Test comparison**: Create multiple baselines and compare
3. **Document your workflow**: Define when/why baselines are created
4. **Set up monitoring**: Monitor task success rates
5. **Plan retention**: Decide how long to keep historical baselines

## 🔗 Additional Resources

- **Full Documentation**: `BASELINE_FEATURE.md`
- **Implementation Details**: `BASELINE_IMPLEMENTATION_SUMMARY.md`
- **Architecture Diagrams**: `BASELINE_ARCHITECTURE.md`
- **Code Examples**: `backend/examples/baseline_usage_examples.py`
- **Comparison Utilities**: `backend/app/services/baseline_comparison.py`

## 💡 Pro Tips

1. **Use descriptive notes**: Always include date and reason in notes field
2. **Baseline before AND after**: Create baselines on both sides of changes
3. **Keep multiple versions**: Don't delete old baselines immediately
4. **Compare normalized data**: Use `use_normalized=True` for cleaner diffs
5. **Schedule during off-hours**: Baseline when devices are less busy
6. **Start small**: Test with 1-2 devices before baselining entire network

## 🎯 Success Checklist

- ☐ Database migration completed
- ☐ Celery worker restarted
- ☐ First baseline created successfully
- ☐ Baselines visible in database
- ☐ Comparison script runs without errors
- ☐ Scheduled task configured (if desired)
- ☐ Documented baseline workflow for team

---

**Need Help?** Check the detailed documentation in `BASELINE_FEATURE.md` or review the code examples in `backend/examples/baseline_usage_examples.py`.
