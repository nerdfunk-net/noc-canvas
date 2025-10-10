# Scheduled Task Ownership & Security Implementation

## Overview

This implementation adds proper ownership tracking and security validation for scheduled (periodic) background tasks. It solves the credential lookup problem and prevents security issues where users could spoof usernames to use other users' credentials.

## Architecture

### 1. **Database Layer** - `ScheduledTaskOwner` Model

**File:** `backend/app/models/scheduled_task_owner.py`

A new table tracks ownership of scheduled tasks:

```python
class ScheduledTaskOwner(Base):
    __tablename__ = "scheduled_task_owners"
    
    id = Column(Integer, primary_key=True)
    periodic_task_id = Column(Integer, unique=True)  # Links to celery's PeriodicTask
    owner_username = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

**Key Features:**
- Explicit ownership tracking separate from celery's schema
- Foreign key relationship to User table
- Indexed for efficient queries

### 2. **API Layer** - Scheduler Endpoints

**File:** `backend/app/api/scheduler.py`

**Changes:**

#### Create Task Endpoint (`POST /api/scheduler/tasks`):
- Automatically injects `username` into task kwargs
- Creates `ScheduledTaskOwner` record after task creation
- Returns owner information in response

#### List Tasks Endpoint (`GET /api/scheduler/tasks`):
- Includes `owner_username` for each task in response
- Looks up ownership from `scheduled_task_owners` table

#### Get Task Endpoint (`GET /api/scheduler/tasks/{id}`):
- Includes `owner_username` in response

#### Delete Task Endpoint (`DELETE /api/scheduler/tasks/{id}`):
- Deletes both the periodic task AND the ownership record

### 3. **Security Layer** - Task Validation

**File:** `backend/app/services/task_security.py`

New security utility functions:

```python
def validate_task_username(db, periodic_task_id, username_from_kwargs):
    """
    Validates that username in kwargs matches the task owner.
    Returns: (is_valid, validated_username)
    """
```

**Security Flow:**
1. Task receives username in kwargs (injected by API)
2. Task looks up who actually owns the task
3. If usernames don't match → security violation logged, owner's username used
4. If usernames match → validation passes
5. Ad-hoc (non-scheduled) tasks bypass validation

### 4. **Task Implementation** - Baseline Task

**File:** `backend/app/tasks/baseline_tasks.py`

**Changes:**
- Added `username` parameter to task signature
- Calls `validate_task_username()` before execution
- Uses validated username for credential lookup
- Logs security violations

## How It Works

### Creating a Scheduled Task

```
User (myusername) creates scheduled baseline task
    ↓
API injects: kwargs = {username: "myusername", ...}
    ↓
PeriodicTask record created in celery's table
    ↓
ScheduledTaskOwner record created:
    - periodic_task_id: 123
    - owner_username: "myusername"
    - owner_id: 456
    ↓
Task stored with ownership
```

### Executing a Scheduled Task

```
Celery Beat triggers task at scheduled time
    ↓
Task reads username="myusername" from kwargs
    ↓
Security validation:
    - Query ScheduledTaskOwner for task ID
    - Compare kwargs username vs owner username
    - Log warning if mismatch
    - Use owner's username (not kwargs)
    ↓
Look up credentials for validated username
    ↓
Execute task with correct user's credentials
```

### Security Protection

**Attack Scenario:** Malicious user edits task kwargs to:
```json
{"username": "admin", "inventory_id": 5}
```

**Protection:**
1. Task validates: kwargs says "admin" but owner is "attacker"
2. Security violation logged
3. Task uses owner's username ("attacker") instead
4. Attacker cannot use admin's credentials ✅

## Database Migration

**Auto-migration:** Table is created automatically on startup via `Base.metadata.create_all()`

**Manual migration script:** `backend/app/migrations/add_scheduled_task_owners.py`

Run manually if needed:
```bash
cd backend
python -m app.migrations.add_scheduled_task_owners
```

## API Response Changes

### PeriodicTaskResponse Schema

**Added field:**
```python
owner_username: Optional[str] = None  # Username of task creator
```

**Example Response:**
```json
{
  "id": 123,
  "name": "Daily Baseline",
  "task": "app.tasks.baseline_tasks.create_baseline",
  "schedule_type": "crontab",
  "enabled": true,
  "owner_username": "myusername",  ← NEW
  ...
}
```

## Benefits

### 1. **Security**
- ✅ Prevents credential spoofing attacks
- ✅ Explicit ownership tracking
- ✅ Audit trail of who created tasks
- ✅ Username validation at execution time

### 2. **Multi-User Support**
- ✅ Each user's tasks use their own credentials
- ✅ Users can see who owns each scheduled task
- ✅ Admin can identify tasks by user

### 3. **Credential Lookup**
- ✅ Automatic username injection
- ✅ Correct credentials used for scheduled tasks
- ✅ No manual configuration needed

### 4. **Maintainability**
- ✅ Separate table (doesn't modify external library)
- ✅ Backward compatible (old tasks still work)
- ✅ Clean separation of concerns

## Testing

### Test Scenarios

1. **Create Scheduled Task**
   - Create task as user "alice"
   - Verify `scheduled_task_owners` record created
   - Verify API response includes `owner_username: "alice"`

2. **Execute Scheduled Task**
   - Task runs automatically via Celery Beat
   - Verify logs show validated username
   - Verify task uses alice's credentials

3. **Security Validation**
   - Manually modify task kwargs username (database edit)
   - Run task
   - Verify security warning logged
   - Verify task uses owner's username (not modified one)

4. **List Tasks**
   - Call `GET /api/scheduler/tasks`
   - Verify each task shows its owner

5. **Delete Task**
   - Delete scheduled task
   - Verify both PeriodicTask and ScheduledTaskOwner deleted

## Files Modified/Created

### Created:
- `backend/app/models/scheduled_task_owner.py` - Ownership model
- `backend/app/services/task_security.py` - Security validation
- `backend/app/migrations/add_scheduled_task_owners.py` - Migration script

### Modified:
- `backend/app/api/scheduler.py` - Added ownership tracking to all endpoints
- `backend/app/tasks/baseline_tasks.py` - Added security validation
- `backend/app/models/__init__.py` - Import new model

## Future Enhancements

1. **UI Display**: Show task owner in frontend scheduler UI
2. **Filtering**: Filter tasks by owner in API
3. **Permissions**: Only allow users to delete their own tasks
4. **Bulk Operations**: Migrate old tasks to add ownership records
5. **Other Tasks**: Add validation to topology_tasks, etc.

## Summary

This implementation provides a **secure, scalable, and maintainable** solution for tracking scheduled task ownership. It prevents credential spoofing while maintaining compatibility with the existing celery-sqlalchemy-scheduler library.

**Key Innovation:** Hybrid approach using both kwargs (for task execution) and a separate tracking table (for ownership/security), giving us the best of both worlds.
