# Baseline Feature Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                            │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────┐             │
│  │ Scheduler  │  │  Dashboard  │  │ Jobs Monitor │             │
│  │    UI      │  │     UI      │  │      UI      │             │
│  └─────┬──────┘  └──────┬──────┘  └──────┬───────┘             │
└────────┼─────────────────┼─────────────────┼───────────────────┘
         │                 │                 │
         └────────┬────────┴────────┬────────┘
                  │                 │
         ┌────────▼─────────────────▼────────┐
         │         FastAPI Backend           │
         │  ┌─────────────────────────────┐  │
         │  │  /api/scheduler/jobs        │  │ Create baseline task
         │  │  /api/scheduler/available   │  │ List available tasks
         │  │  /api/jobs/{id}             │  │ Monitor task status
         │  └────────────┬────────────────┘  │
         └───────────────┼───────────────────┘
                         │
         ┌───────────────▼───────────────────┐
         │      Celery Background Tasks      │
         │  ┌─────────────────────────────┐  │
         │  │ baseline_tasks.py           │  │
         │  │  • create_baseline()        │  │
         │  │  • Device iteration         │  │
         │  │  • Command execution        │  │
         │  │  • Normalization            │  │
         │  │  • Database storage         │  │
         │  └────────┬───────┬────────────┘  │
         └───────────┼───────┼───────────────┘
                     │       │
         ┌───────────▼───┐   │   ┌──────────────────┐
         │  Device Comm  │   │   │ Nautobot Service │
         │   Service     │   │   │                  │
         │ • SSH Connect │   └──▶│ • Get devices    │
         │ • Execute CMD │       │ • Get device info│
         │ • Parse TextFSM│      └──────────────────┘
         └───────────────┘
                 │
         ┌───────▼────────────────────────────────────┐
         │          Network Devices                   │
         │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  │
         │  │Router│  │Switch│  │  FW  │  │  ...  │  │
         │  └──────┘  └──────┘  └──────┘  └──────┘  │
         └────────────────────────────────────────────┘
                 │
                 │ Command output
                 ▼
         ┌───────────────────────────────────────────┐
         │      Database (PostgreSQL)                │
         │  ┌─────────────────────────────────────┐  │
         │  │      baseline_cache table           │  │
         │  ├─────────────────────────────────────┤  │
         │  │ id | device_id | command | raw_..  │  │
         │  │  1 | uuid-123  | show int| {...}   │  │
         │  │  2 | uuid-123  | show arp| {...}   │  │
         │  │  3 | uuid-456  | show int| {...}   │  │
         │  └─────────────────────────────────────┘  │
         └───────────────────────────────────────────┘
                 │
         ┌───────▼────────────────────────────────────┐
         │    Baseline Comparison Service             │
         │  • Get baseline versions                   │
         │  • Compare normalized data                 │
         │  • Generate diff reports                   │
         │  • Detect configuration drift              │
         └────────────────────────────────────────────┘
```

## Data Flow: Creating a Baseline

```
1. User Action
   └─▶ [Scheduler UI] "Create Baseline Task"
          │
          ├─ Device IDs: ["device1", "device2"]
          ├─ Commands: ["show interfaces", "show cdp neighbors", ...]
          └─ Notes: "Pre-upgrade baseline"

2. Task Submission
   └─▶ [FastAPI] POST /api/scheduler/jobs
          │
          └─▶ [Celery] send_task("create_baseline")
                 │
                 └─ Task ID: abc-123

3. Task Execution (Per Device)
   └─▶ [Celery Worker]
          │
          ├─ Get device info from Nautobot
          │     └─▶ [Nautobot API] GET /devices/{id}
          │            └─ Returns: name, IP, platform, network_driver
          │
          ├─ For each command:
          │     │
          │     ├─ Execute command on device
          │     │     └─▶ [Device Comm Service]
          │     │            └─▶ SSH to device.primary_ip
          │     │                   └─ Run: "show interfaces"
          │     │                         └─ Parse with TextFSM
          │     │                               └─ Returns: [{"interface": "Gi0/1", ...}]
          │     │
          │     ├─ Normalize output
          │     │     └─▶ [_normalize_output()]
          │     │            ├─ Remove: counters, timestamps, rates
          │     │            ├─ Sort: entries consistently
          │     │            └─ Returns: cleaned JSON
          │     │
          │     └─ Store in database
          │           └─▶ [Database]
          │                  ├─ Check if baseline exists
          │                  ├─ If exists: UPDATE + version++
          │                  └─ If not: INSERT new record
          │
          └─ Return results
                └─ devices_processed: 2/2
                └─ total_commands: 14
                └─ baseline_ids: [1, 2, 3, ...]
```

## Data Flow: Comparing Baselines

```
1. Query Baseline History
   └─▶ [Database] SELECT * FROM baseline_cache
                  WHERE device_id = 'uuid-123'
                    AND command = 'show interfaces'
                  ORDER BY baseline_version DESC

2. Retrieve Two Versions
   ├─ baseline_old (version 1)
   │     ├─ created_at: 2025-10-01
   │     ├─ notes: "Initial baseline"
   │     └─ normalized_output: [{"interface": "Gi0/1", "status": "up"}, ...]
   │
   └─ baseline_new (version 2)
         ├─ created_at: 2025-10-10
         ├─ notes: "Post-upgrade baseline"
         └─ normalized_output: [{"interface": "Gi0/1", "status": "down"}, ...]

3. Comparison Process
   └─▶ [BaselineComparator.compare_baselines()]
          │
          ├─ Parse JSON data
          │     ├─ old_data = json.loads(baseline_old.normalized_output)
          │     └─ new_data = json.loads(baseline_new.normalized_output)
          │
          ├─ Identify items by key
          │     └─ Key field: "interface"
          │
          ├─ Calculate differences
          │     ├─ Added: new_keys - old_keys
          │     ├─ Removed: old_keys - new_keys
          │     └─ Changed: compare common items field-by-field
          │
          └─ Generate report
                └─ {
                     "has_changes": true,
                     "summary": {
                       "items_added": 1,
                       "items_removed": 0,
                       "items_changed": 2
                     },
                     "differences": {
                       "added": [...],
                       "removed": [...],
                       "changed": [
                         {
                           "interface": "Gi0/1",
                           "changes": {
                             "status": {"old": "up", "new": "down"}
                           }
                         }
                       ]
                     }
                   }
```

## Normalization Process

```
Raw Output (from TextFSM)
   │
   ├─ Interface: GigabitEthernet0/1
   ├─ Status: up
   ├─ Protocol: up
   ├─ Description: Uplink
   ├─ input_rate: 1234567 ◄─── DYNAMIC (changes constantly)
   ├─ output_rate: 9876543 ◄─── DYNAMIC
   ├─ input_packets: 1234567890 ◄─── DYNAMIC
   ├─ output_packets: 9876543210 ◄─── DYNAMIC
   ├─ last_input: 00:00:01 ◄─── DYNAMIC
   └─ last_output: 00:00:02 ◄─── DYNAMIC
          │
          │ [_normalize_output()]
          ▼
Normalized Output
   │
   ├─ Interface: GigabitEthernet0/1 ◄─── KEPT
   ├─ Status: up ◄─── KEPT (configuration-relevant)
   ├─ Protocol: up ◄─── KEPT
   └─ Description: Uplink ◄─── KEPT
          │
          ├─ (input_rate removed)
          ├─ (output_rate removed)
          ├─ (counters removed)
          └─ (timestamps removed)
          │
          │ Sorted alphabetically
          │ Whitespace normalized
          ▼
   JSON stored in normalized_output column
```

## Comparison Algorithm

```
Step 1: Parse Data
   old_data = [
     {"interface": "Gi0/1", "status": "up", "desc": "Uplink"},
     {"interface": "Gi0/2", "status": "up", "desc": "Backup"}
   ]
   new_data = [
     {"interface": "Gi0/1", "status": "down", "desc": "Uplink"},
     {"interface": "Gi0/3", "status": "up", "desc": "New Link"}
   ]

Step 2: Convert to Dicts by Key
   old_dict = {
     "Gi0/1": {"interface": "Gi0/1", "status": "up", "desc": "Uplink"},
     "Gi0/2": {"interface": "Gi0/2", "status": "up", "desc": "Backup"}
   }
   new_dict = {
     "Gi0/1": {"interface": "Gi0/1", "status": "down", "desc": "Uplink"},
     "Gi0/3": {"interface": "Gi0/3", "status": "up", "desc": "New Link"}
   }

Step 3: Calculate Set Differences
   old_keys = {"Gi0/1", "Gi0/2"}
   new_keys = {"Gi0/1", "Gi0/3"}
   
   added = {"Gi0/3"}
   removed = {"Gi0/2"}
   common = {"Gi0/1"}

Step 4: Compare Common Items Field-by-Field
   For "Gi0/1":
     old: {"status": "up", "desc": "Uplink"}
     new: {"status": "down", "desc": "Uplink"}
     
     changes: {
       "status": {"old": "up", "new": "down"}
     }

Step 5: Generate Result
   {
     "has_changes": true,
     "summary": {
       "items_added": 1,      # Gi0/3
       "items_removed": 1,    # Gi0/2
       "items_changed": 1,    # Gi0/1
       "items_unchanged": 0
     },
     "differences": {
       "added": [{"interface": "Gi0/3", ...}],
       "removed": [{"interface": "Gi0/2", ...}],
       "changed": [{
         "interface": "Gi0/1",
         "changes": {"status": {"old": "up", "new": "down"}}
       }]
     }
   }
```

## Database Schema Visualization

```
┌─────────────────────────────────────────────────────────────────┐
│                    baseline_cache table                          │
├─────────────────────────────────────────────────────────────────┤
│ Columns:                                                         │
│   id                  INTEGER PRIMARY KEY                        │
│   device_id           VARCHAR (indexed) ──┐                     │
│   device_name         VARCHAR (indexed)   │                     │
│   command             VARCHAR ─────────────┤                     │
│   raw_output          TEXT (JSON)          │                     │
│   normalized_output   TEXT (JSON)          │                     │
│   created_at          TIMESTAMP            │                     │
│   updated_at          TIMESTAMP (indexed) ─┤                     │
│   baseline_version    INTEGER              │                     │
│   notes               VARCHAR              │                     │
├─────────────────────────────────────────────┴───────────────────┤
│ Indexes:                                                         │
│   ix_baseline_device_command (device_id, command) ◄─ UNIQUE     │
│   ix_baseline_device_updated (device_id, updated_at)            │
│   ix_baseline_device_name (device_name)                         │
└──────────────────────────────────────────────────────────────────┘

Example Data:
┌────┬─────────────┬──────────────┬─────────────┬────────┬──────────┬────────┐
│ id │  device_id  │ device_name  │   command   │version │updated_at│  notes │
├────┼─────────────┼──────────────┼─────────────┼────────┼──────────┼────────┤
│  1 │ uuid-abc-123│ router1      │show int     │   1    │2025-10-01│Initial │
│  2 │ uuid-abc-123│ router1      │show int     │   2    │2025-10-08│Weekly  │
│  3 │ uuid-abc-123│ router1      │show cdp neig│   1    │2025-10-01│Initial │
│  4 │ uuid-abc-123│ router1      │show ip arp  │   1    │2025-10-01│Initial │
│  5 │ uuid-def-456│ switch1      │show int     │   1    │2025-10-01│Initial │
└────┴─────────────┴──────────────┴─────────────┴────────┴──────────┴────────┘
```

## Integration Points

```
┌─────────────────────────────────────────────────────────────┐
│                    Existing Systems                          │
└────┬────────────────────┬─────────────────┬─────────────────┘
     │                    │                 │
     │                    │                 │
┌────▼────────┐  ┌────────▼──────┐  ┌──────▼──────────┐
│  Nautobot   │  │ Device Comm   │  │   Topology      │
│  Service    │  │   Service     │  │   Discovery     │
│             │  │               │  │                 │
│ • Devices   │  │ • SSH/Netmiko │  │ • Commands      │
│ • Locations │  │ • TextFSM     │  │ • Parsing       │
│ • Platforms │  │ • Credentials │  │ • Caching       │
└─────────────┘  └───────────────┘  └─────────────────┘
     │                    │                 │
     │                    │                 │
     └────────┬───────────┴────────┬────────┘
              │                    │
              │                    │
     ┌────────▼────────────────────▼────────┐
     │        Baseline Feature              │
     │                                      │
     │  ┌────────────────────────────────┐  │
     │  │ baseline_tasks.py              │  │
     │  │  • Reuses topology commands    │  │
     │  │  • Uses device communication   │  │
     │  │  • Stores in database          │  │
     │  └────────────────────────────────┘  │
     │                                      │
     │  ┌────────────────────────────────┐  │
     │  │ baseline_comparison.py         │  │
     │  │  • Compares versions           │  │
     │  │  • Generates reports           │  │
     │  └────────────────────────────────┘  │
     └──────────────────────────────────────┘
```
