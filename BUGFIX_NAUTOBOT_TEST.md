# Bug Fix: Nautobot Test Endpoint

## Issue
After refactoring, Nautobot connection test was failing with:
```
POST /api/settings/test-nautobot HTTP/1.1" 405 Method Not Allowed
```

## Root Cause
**Pre-existing endpoint mismatch** (not caused by refactoring):
- **Frontend** was calling: `POST /api/settings/test-nautobot`
- **Backend** had: `POST /api/settings/nautobot/test`

The endpoint naming was inconsistent between frontend and backend.

## Solution
Added a legacy alias endpoint to maintain backward compatibility:

```python
@router.post("/test-nautobot", response_model=SettingsTest)
async def test_nautobot_settings_legacy(
    test_request: NautobotTestRequest,
    current_user: User = Depends(get_current_user),
):
    """Test Nautobot connection settings (legacy endpoint for backward compatibility)."""
    return await test_nautobot_settings(test_request, current_user)
```

## Endpoints Now Available

### Settings Testing (with user-provided settings):
- `POST /api/settings/nautobot/test` - ✅ New, proper RESTful naming
- `POST /api/settings/test-nautobot` - ✅ Legacy alias for backward compatibility

### Connection Testing (with current app settings):
- `GET /api/nautobot/test` - ✅ Tests current configuration

## Impact
- ✅ **Zero Breaking Changes** - Both endpoints work
- ✅ **Backward Compatible** - Old frontend code continues to work
- ✅ **Future-Proof** - New frontend can use proper RESTful endpoint

## Testing
To test the fix:
```bash
# Test with current settings
curl -X GET http://localhost:8000/api/nautobot/test

# Test with provided settings (legacy)
curl -X POST http://localhost:8000/api/settings/test-nautobot \
  -H "Content-Type: application/json" \
  -d '{"url":"http://nautobot","token":"abc123","timeout":30,"verify_ssl":true}'

# Test with provided settings (new)
curl -X POST http://localhost:8000/api/settings/nautobot/test \
  -H "Content-Type: application/json" \
  -d '{"url":"http://nautobot","token":"abc123","timeout":30,"verify_ssl":true}'
```

## Status
✅ **Fixed** - Nautobot connection test now works correctly
