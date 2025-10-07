# Icon Encoding Fix

## Issue
The device context menu was displaying corrupted emoji characters (showing as � question marks) for:
- "Interfaces" menu item (was: �)
- "Commands" menu item (was: �💻)

## Root Cause
Emoji encoding corruption in the source file, likely from copy/paste or file encoding issues.

## Solution
Fixed the corrupted emoji icons in the context menu:

**File**: `frontend/src/components/NOCCanvas.vue`

- Line 1630: Changed `icon: '�'` to `icon: '🔌'` (plug emoji for Interfaces)
- Line 1639: Changed `icon: '�💻'` to `icon: '💻'` (computer emoji for Commands)

## Result
Context menu now displays correctly with proper emojis:
- 🔌 Interfaces
- 💻 Commands

## Date
October 7, 2025
