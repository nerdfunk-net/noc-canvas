# Canvas Layer Support - Implementation Guide

## Overview

The NOC Canvas now supports **Konva.js layers** with two distinct layers:
1. **Background Layer** - Renders behind devices (for backgrounds, regions, etc.)
2. **Devices Layer** - Renders above background (for devices and foreground shapes)

## Architecture

### Layer Hierarchy (Bottom to Top)
```
1. Grid Layer (optional, for reference grid)
2. Background Layer ← New! (shapes with layer='background')
3. Connections Layer (device connections)
4. Devices Layer (devices)
5. Shapes Layer ← New! (shapes with layer='devices')
6. Selection Layer (selection boxes)
```

## Backend Changes

### 1. Database Schema
**File**: `backend/app/models/shape.py`

Added `layer` column to shapes table:
```python
layer = Column(String, default="devices", nullable=False)  # 'background' or 'devices'
```

**Migration**: `backend/migrations/001_add_layer_to_shapes.sql`
- Adds `layer` column with default value `'devices'`
- Creates index on `layer` for query performance
- Non-breaking change (existing shapes get default value)

### 2. API Endpoints
**File**: `backend/app/api/shapes.py`

Updated Pydantic models to include `layer` field:
```python
class ShapeCreate(BaseModel):
    # ... existing fields ...
    layer: str = "devices"  # 'background' or 'devices'

class ShapeUpdate(BaseModel):
    # ... existing fields ...
    layer: str | None = None

class ShapeResponse(BaseModel):
    # ... existing fields ...
    layer: str
```

All shape CRUD endpoints now support the `layer` parameter.

## Frontend Changes

### 1. Shape Interface
**File**: `frontend/src/stores/shapes.ts`

Updated Shape interface:
```typescript
export interface Shape {
  // ... existing fields ...
  layer?: string // 'background' or 'devices'
}
```

### 2. Canvas Component
**File**: `frontend/src/components/NOCCanvas.vue`

#### Added Computed Properties:
```typescript
// Separate shapes by layer
const backgroundShapes = computed(() => {
  return shapesStore.shapes.filter(shape => shape.layer === 'background')
})

const deviceLayerShapes = computed(() => {
  return shapesStore.shapes.filter(shape => shape.layer !== 'background')
})
```

#### Layer Structure:
```vue
<!-- Background Shapes Layer (renders behind devices) -->
<v-layer ref="backgroundLayer">
  <v-group v-for="shape in backgroundShapes" ... />
</v-layer>

<!-- Connections Layer -->
<v-layer ref="connectionsLayer">...</v-layer>

<!-- Devices Layer (renders above background) -->
<v-layer ref="devicesLayer">...</v-layer>

<!-- Device Shapes Layer (renders above devices) -->
<v-layer ref="shapesLayer">
  <v-group v-for="shape in deviceLayerShapes" ... />
</v-layer>
```

### 3. Symbols Panel
**File**: `frontend/src/components/SymbolsPanel.vue`

Shapes now default to `background` layer:
```typescript
const shapes = ref<Symbol[]>([
  { ..., shapeType: 'rectangle', layer: 'background' },
  { ..., shapeType: 'circle', layer: 'background' },
])
```

### 4. Drop Handler
**File**: `frontend/src/components/NOCCanvas.vue`

Updated shape creation to include layer:
```typescript
shapesStore.createShape({
  // ... existing fields ...
  layer: symbol.layer || 'background', // Default to background layer
})
```

## Usage

### Creating Background Shapes

1. Drag a **Rectangle** or **Circle** from the Symbols Panel
2. Drop it on the canvas
3. It will automatically be placed on the **background layer**
4. Background shapes render **behind devices**

### Layer Behavior

- **Background Layer**: Perfect for:
  - Network regions/zones
  - Geographic areas
  - Background decorations
  - Organizational boundaries

- **Devices Layer**: Perfect for:
  - Annotations
  - Labels
  - Callouts
  - Foreground highlights

### Changing Shape Layer

To change a shape's layer after creation, you can:
1. Use the API to update the shape's `layer` property
2. Currently set in SymbolsPanel when dragging from palette

## Migration Guide

### Running the Migration

```bash
# Method 1: Using Python script
cd backend
python3 run_migration.py

# Method 2: Using psql directly
psql -U <username> -d <database> -f migrations/001_add_layer_to_shapes.sql
```

### Backwards Compatibility

- ✅ Existing shapes get default `layer='devices'` value
- ✅ API remains backwards compatible (layer is optional)
- ✅ No breaking changes to existing functionality

## Future Enhancements

Potential improvements:
- [ ] Layer visibility toggle in UI
- [ ] Layer locking (prevent editing)
- [ ] Additional layer types (annotations, labels, etc.)
- [ ] Layer opacity controls
- [ ] Context menu option to change shape layer
- [ ] Layer management panel in UI

## Testing

### Verify Layer Support

1. **Backend**: Check shape model includes layer field
   ```bash
   curl -H "Authorization: Bearer <token>" http://localhost:8000/api/shapes
   ```

2. **Frontend**: Drop shapes on canvas and verify rendering order:
   - Background shapes should be behind devices
   - Device layer shapes should be above devices

3. **Database**: Verify column exists
   ```sql
   \d shapes
   -- Should show 'layer' column with default 'devices'
   ```

## Files Modified

### Backend
- `backend/app/models/shape.py` - Added layer column
- `backend/app/api/shapes.py` - Added layer to API models
- `backend/migrations/001_add_layer_to_shapes.sql` - Database migration
- `backend/run_migration.py` - Migration runner script

### Frontend
- `frontend/src/stores/shapes.ts` - Added layer to Shape interface
- `frontend/src/components/NOCCanvas.vue` - Implemented layer rendering
- `frontend/src/components/SymbolsPanel.vue` - Added layer to symbols

## Support

For issues or questions:
- Check migration logs in `backend/migrations/README.md`
- Verify database migration completed successfully
- Check browser console for frontend errors
- Verify shapes have `layer` field in API responses
