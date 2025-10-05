# Network Topology Builder - Implementation Plan

## Overview

Build network topology from cached CDP neighbor data and routing information. This is the core feature of the NOC Canvas application - automatically discovering and visualizing network device relationships.

## Database Structure Analysis ✅

The database has all necessary data for topology building:

**Existing Cache Tables:**
1. ✅ **DeviceCache** - Device information (device_id, device_name, primary_ip)
2. ✅ **InterfaceCache** - Interface details (interface_name, mac_address, status)
3. ✅ **IPAddressCache** - IP addresses on interfaces
4. ✅ **CDPNeighborCache** - CDP/LLDP neighbor relationships:
   - `neighbor_name`, `neighbor_ip`
   - `local_interface`, `neighbor_interface`
   - Platform, capabilities
5. ✅ **StaticRouteCache** - Static routes (network, nexthop_ip, interface_name)
6. ✅ **OSPFRouteCache** - OSPF routes (network, nexthop_ip, area, route_type)
7. ✅ **BGPRouteCache** - BGP routes (network, nexthop_ip, as_path)
8. ✅ **ARPCache** - ARP tables (ip_address, mac_address, interface_name)
9. ✅ **MACAddressTableCache** - MAC tables (mac_address, vlan_id, interface_name)

**Key Relationships for Topology:**
- CDP neighbors: Direct Layer 2/3 physical connectivity
- Routing tables: Layer 3 logical paths
- ARP + MAC tables: Device discovery via learned addresses
- IP addresses: Interface connectivity mapping

---

## Phase 1: Backend Topology Service 🎯

### 1.1 Create Topology Data Models & Schemas
**File:** `backend/app/schemas/topology.py`

```python
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from enum import Enum

class LinkType(str, Enum):
    CDP_NEIGHBOR = "cdp_neighbor"
    LAYER3_ROUTE = "layer3_route"
    ARP_DISCOVERED = "arp_discovered"
    MAC_TABLE = "mac_table"

class TopologyNode(BaseModel):
    device_id: str
    device_name: str
    primary_ip: Optional[str]
    platform: Optional[str]
    device_type: Optional[str]
    position_x: Optional[float]
    position_y: Optional[float]
    metadata: Optional[Dict[str, Any]]

class TopologyLink(BaseModel):
    source_device_id: str
    target_device_id: str
    source_device_name: str
    target_device_name: str
    source_interface: Optional[str]
    target_interface: Optional[str]
    link_type: LinkType
    link_metadata: Optional[Dict[str, Any]]  # route info, metric, etc.

class TopologyGraph(BaseModel):
    nodes: List[TopologyNode]
    links: List[TopologyLink]
    metadata: Optional[Dict[str, Any]]
```

### 1.2 Create Topology Builder Service
**File:** `backend/app/services/topology_builder_service.py`

**Core Methods:**
```python
class TopologyBuilderService:

    # Primary Methods
    @staticmethod
    def build_topology_from_cache(
        db: Session,
        device_ids: Optional[List[str]] = None,
        include_cdp: bool = True,
        include_routing: bool = False,
        route_types: List[str] = ["static", "ospf", "bgp"],
        include_layer2: bool = False,
        auto_layout: bool = True
    ) -> TopologyGraph:
        """Build complete topology from cache data."""

    @staticmethod
    def build_cdp_topology(
        db: Session,
        device_ids: Optional[List[str]] = None
    ) -> TopologyGraph:
        """Build topology from CDP/LLDP neighbors only."""

    @staticmethod
    def build_routing_topology(
        db: Session,
        device_ids: Optional[List[str]] = None,
        route_types: List[str] = ["static", "ospf", "bgp"]
    ) -> TopologyGraph:
        """Build topology from routing tables."""

    @staticmethod
    def build_layer2_topology(
        db: Session,
        device_ids: Optional[List[str]] = None
    ) -> TopologyGraph:
        """Build topology from MAC/ARP tables."""

    # Helper Methods
    @staticmethod
    def _extract_cdp_links(
        db: Session,
        devices: List[DeviceCache]
    ) -> List[TopologyLink]:
        """Extract links from CDP neighbor cache."""

    @staticmethod
    def _extract_routing_links(
        db: Session,
        devices: List[DeviceCache],
        route_types: List[str]
    ) -> List[TopologyLink]:
        """Extract links from routing tables."""

    @staticmethod
    def _extract_arp_links(
        db: Session,
        devices: List[DeviceCache]
    ) -> List[TopologyLink]:
        """Extract links from ARP cache."""

    @staticmethod
    def _extract_mac_table_links(
        db: Session,
        devices: List[DeviceCache]
    ) -> List[TopologyLink]:
        """Extract links from MAC address tables."""

    @staticmethod
    def _resolve_neighbor_device_id(
        db: Session,
        neighbor_name: str,
        neighbor_ip: Optional[str]
    ) -> Optional[str]:
        """Resolve neighbor name/IP to device_id in cache."""

    @staticmethod
    def _deduplicate_links(links: List[TopologyLink]) -> List[TopologyLink]:
        """Remove duplicate bidirectional links."""

    @staticmethod
    def _calculate_layout_positions(
        nodes: List[TopologyNode],
        links: List[TopologyLink]
    ) -> Dict[str, tuple]:
        """Calculate x/y positions for nodes using graph layout algorithm."""
```

**Topology Building Logic:**

1. **CDP-Based Topology** (Layer 2/3 Physical):
   - Query all CDPNeighborCache entries for selected devices
   - For each CDP entry:
     - Match neighbor_name/neighbor_ip to DeviceCache to find neighbor device_id
     - Create bidirectional link: (device_id, local_interface) ↔ (neighbor_device_id, neighbor_interface)
   - Filter out unresolved neighbors (not in cache)

2. **Routing-Based Topology** (Layer 3 Logical):
   - Query routing caches (Static/OSPF/BGP) for selected devices
   - For each route:
     - Find which device owns nexthop_ip (via IPAddressCache)
     - Create directional link: (source_device, interface) → (nexthop_device, interface)
   - Support filtering by route type (static/ospf/bgp)

3. **Layer 2 Discovery** (MAC/ARP):
   - Cross-reference ARP cache (device learned IP→MAC)
   - Find MAC in MACAddressTableCache (which switch port learned MAC)
   - Trace path: Device A → Switch Port → Device B

4. **Auto-Layout Algorithm:**
   - Use force-directed graph (spring layout)
   - Or hierarchical layout (core/distribution/access layers)
   - Return x/y coordinates for each node

### 1.3 Create Topology API Endpoints
**File:** `backend/app/api/topology.py`

```python
from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.topology import TopologyGraph
from app.services.topology_builder_service import TopologyBuilderService

router = APIRouter(prefix="/topology", tags=["topology"])

# Main topology endpoints
@router.get("/build", response_model=TopologyGraph)
async def build_topology(
    device_ids: Optional[List[str]] = Query(None),
    include_cdp: bool = True,
    include_routing: bool = False,
    route_types: List[str] = Query(["static", "ospf", "bgp"]),
    include_layer2: bool = False,
    auto_layout: bool = True,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Build topology from cached data."""

@router.get("/cdp", response_model=TopologyGraph)
async def get_cdp_topology(
    device_ids: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get CDP-based topology only."""

@router.get("/routing", response_model=TopologyGraph)
async def get_routing_topology(
    device_ids: Optional[List[str]] = Query(None),
    route_types: List[str] = Query(["static", "ospf", "bgp"]),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get routing-based topology."""

@router.get("/layer2", response_model=TopologyGraph)
async def get_layer2_topology(
    device_ids: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get Layer 2 topology from MAC/ARP tables."""

# Utility endpoints
@router.post("/resolve-neighbor")
async def resolve_neighbor(
    neighbor_name: str,
    neighbor_ip: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Resolve neighbor name/IP to device_id."""

@router.get("/statistics")
async def get_topology_statistics(
    device_ids: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get topology statistics."""
```

### 1.4 Register Topology Router
**File:** `backend/app/main.py`

Add to router imports:
```python
from app.api import topology
app.include_router(topology.router, prefix="/api")
```

---

## Phase 2: Frontend Topology Visualization 🎨

### 2.1 Topology Store (State Management)
**File:** `frontend/src/stores/topology.ts` (if using Pinia)

```typescript
import { defineStore } from 'pinia'
import { makeAuthenticatedRequest } from '@/utils/api'

interface TopologyNode {
  device_id: string
  device_name: string
  primary_ip?: string
  platform?: string
  device_type?: string
  position_x?: number
  position_y?: number
  metadata?: Record<string, any>
}

interface TopologyLink {
  source_device_id: string
  target_device_id: string
  source_device_name: string
  target_device_name: string
  source_interface?: string
  target_interface?: string
  link_type: 'cdp_neighbor' | 'layer3_route' | 'arp_discovered' | 'mac_table'
  link_metadata?: Record<string, any>
}

interface TopologyGraph {
  nodes: TopologyNode[]
  links: TopologyLink[]
  metadata?: Record<string, any>
}

export const useTopologyStore = defineStore('topology', {
  state: () => ({
    topologyNodes: [] as TopologyNode[],
    topologyLinks: [] as TopologyLink[],
    selectedLinkType: 'all' as string,
    loading: false,
    error: null as string | null
  }),

  actions: {
    async fetchTopology(
      deviceIds?: string[],
      options?: {
        includeCdp?: boolean
        includeRouting?: boolean
        routeTypes?: string[]
        includeLayer2?: boolean
        autoLayout?: boolean
      }
    ) {
      // Implementation
    },

    async fetchCdpTopology(deviceIds?: string[]) {
      // Implementation
    },

    async fetchRoutingTopology(deviceIds?: string[], routeTypes?: string[]) {
      // Implementation
    },

    importTopologyToCanvas() {
      // Implementation - convert topology to canvas shapes/connections
    }
  }
})
```

### 2.2 Topology Builder Modal/View
**File:** `frontend/src/components/TopologyBuilderModal.vue`

**Features:**
- Device selection (multi-select from cached devices)
- Topology type selection:
  - [ ] CDP Neighbors (Layer 2/3 Physical)
  - [ ] Routing (Static/OSPF/BGP)
  - [ ] Layer 2 (MAC/ARP Discovery)
- Route type filters (if routing enabled)
- Auto-layout toggle
- Preview topology graph
- "Import to Canvas" button

**Template Structure:**
```vue
<template>
  <div class="modal">
    <h2>Build Network Topology</h2>

    <!-- Device Selection -->
    <div class="device-selection">
      <label>Select Devices (or leave empty for all cached devices)</label>
      <multi-select v-model="selectedDevices" :options="cachedDevices" />
    </div>

    <!-- Topology Options -->
    <div class="topology-options">
      <label>
        <input type="checkbox" v-model="includeCdp" />
        CDP Neighbors (Physical Connectivity)
      </label>

      <label>
        <input type="checkbox" v-model="includeRouting" />
        Routing Tables (Logical Paths)
      </label>

      <div v-if="includeRouting" class="route-types">
        <label><input type="checkbox" v-model="routeTypes" value="static" /> Static</label>
        <label><input type="checkbox" v-model="routeTypes" value="ospf" /> OSPF</label>
        <label><input type="checkbox" v-model="routeTypes" value="bgp" /> BGP</label>
      </div>

      <label>
        <input type="checkbox" v-model="includeLayer2" />
        Layer 2 Discovery (MAC/ARP)
      </label>

      <label>
        <input type="checkbox" v-model="autoLayout" />
        Auto-calculate layout positions
      </label>
    </div>

    <!-- Topology Preview -->
    <div class="topology-preview">
      <TopologyGraph :nodes="topology.nodes" :links="topology.links" />
    </div>

    <!-- Actions -->
    <div class="actions">
      <button @click="buildTopology">Build Topology</button>
      <button @click="importToCanvas" :disabled="!topology.nodes.length">
        Import to Canvas
      </button>
      <button @click="close">Cancel</button>
    </div>
  </div>
</template>
```

### 2.3 Integration with NOCCanvas
**File:** `frontend/src/components/NOCCanvas.vue`

**New Features:**
- Add "Build Topology" button to toolbar
- Import topology nodes as device shapes
- Import topology links as connections
- Map topology node positions to canvas coordinates
- Optionally: Highlight link types with different colors

**Implementation:**
```typescript
// Add to NOCCanvas methods
async openTopologyBuilder() {
  this.showTopologyBuilderModal = true
}

importTopologyToCanvas(topology: TopologyGraph) {
  // Convert nodes to device shapes
  topology.nodes.forEach(node => {
    this.addDeviceToCanvas({
      device_id: node.device_id,
      device_name: node.device_name,
      position_x: node.position_x || 100,
      position_y: node.position_y || 100,
      // ... other properties
    })
  })

  // Convert links to connections
  topology.links.forEach(link => {
    this.addConnection({
      source_device_id: link.source_device_id,
      target_device_id: link.target_device_id,
      source_interface: link.source_interface,
      target_interface: link.target_interface,
      link_type: link.link_type
    })
  })
}
```

### 2.4 Topology Visualization Component
**File:** `frontend/src/components/TopologyGraph.vue` (Optional preview)

**Features:**
- Lightweight graph preview using D3.js, vis.js, or Cytoscape.js
- Show nodes and links before importing
- Interactive node dragging
- Link filtering by type
- Color coding by device type or link type

**Library Options:**
- **D3.js** - Highly customizable, force-directed layouts
- **vis.js** - Easy to use, good for network graphs
- **Cytoscape.js** - Advanced graph analysis features
- **ELK.js** - Hierarchical layouts

---

## Phase 3: Advanced Features 🚀

### 3.1 Topology Path Analysis
**File:** Add to `backend/app/services/topology_builder_service.py`

```python
@staticmethod
def find_paths(
    db: Session,
    source_device_id: str,
    target_device_id: str,
    max_hops: int = 5
) -> List[List[TopologyLink]]:
    """Find all paths between two devices."""
    # BFS/DFS algorithm

@staticmethod
def find_shortest_path(
    db: Session,
    source_device_id: str,
    target_device_id: str
) -> List[TopologyLink]:
    """Find shortest path using Dijkstra's algorithm."""
```

**API Endpoints:**
```python
@router.get("/paths")
async def find_paths(
    source: str,
    target: str,
    max_hops: int = 5,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Find all paths between two devices."""

@router.get("/shortest-path")
async def find_shortest_path(
    source: str,
    target: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Find shortest path between two devices."""
```

### 3.2 Topology Diff/Change Detection
**File:** Add to `backend/app/services/topology_builder_service.py`

```python
@staticmethod
def compare_topologies(
    previous: TopologyGraph,
    current: TopologyGraph
) -> Dict[str, Any]:
    """Compare two topology snapshots."""
    return {
        "added_nodes": [...],
        "removed_nodes": [...],
        "added_links": [...],
        "removed_links": [...],
        "modified_nodes": [...],
        "modified_links": [...]
    }
```

**API Endpoint:**
```python
@router.post("/compare")
async def compare_topologies(
    previous: TopologyGraph,
    current: TopologyGraph,
    current_user: dict = Depends(get_current_user)
):
    """Compare topology snapshots for changes."""
```

### 3.3 Topology Export
**File:** Add to `backend/app/services/topology_builder_service.py`

```python
@staticmethod
def export_topology(
    topology: TopologyGraph,
    format: str  # json, graphml, dot, cytoscape
) -> str:
    """Export topology to various formats."""
```

**API Endpoint:**
```python
@router.get("/export")
async def export_topology(
    format: str = Query("json", regex="^(json|graphml|dot|cytoscape)$"),
    device_ids: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Export topology to various formats."""
```

### 3.4 Recursive Neighbor Discovery
**File:** Add to `backend/app/services/topology_builder_service.py`

```python
@staticmethod
async def discover_topology_recursive(
    db: Session,
    seed_device_id: str,
    max_depth: int = 3,
    auto_cache: bool = True
) -> TopologyGraph:
    """
    Start from seed device, crawl CDP neighbors recursively.
    Optionally cache all discovered devices.
    """
```

**API Endpoint:**
```python
@router.post("/discover")
async def discover_topology(
    seed_device_id: str,
    max_depth: int = 3,
    auto_cache: bool = True,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Recursively discover network topology from seed device."""
```

---

## Phase 4: Database Enhancements (Optional)

### 4.1 Topology Snapshot Table
**Purpose:** Save/load topology snapshots for change tracking

**Migration:** Create new table
```sql
CREATE TABLE topology_snapshots (
  id SERIAL PRIMARY KEY,
  name VARCHAR NOT NULL,
  description TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  created_by VARCHAR,
  topology_data JSONB NOT NULL,
  device_count INTEGER,
  link_count INTEGER,
  metadata JSONB
);

CREATE INDEX idx_topology_snapshots_created_at ON topology_snapshots(created_at DESC);
```

**Model:** `backend/app/models/topology.py`
```python
class TopologySnapshot(Base):
    __tablename__ = "topology_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String)
    topology_data = Column(JSON, nullable=False)
    device_count = Column(Integer)
    link_count = Column(Integer)
    metadata = Column(JSON)
```

**API Endpoints:**
```python
@router.post("/snapshots")
async def save_snapshot(
    name: str,
    topology: TopologyGraph,
    description: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Save topology snapshot."""

@router.get("/snapshots")
async def list_snapshots(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all topology snapshots."""

@router.get("/snapshots/{snapshot_id}")
async def get_snapshot(
    snapshot_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get specific topology snapshot."""

@router.delete("/snapshots/{snapshot_id}")
async def delete_snapshot(
    snapshot_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete topology snapshot."""
```

---

## Implementation Sequence

### **Step 1: Backend Foundation** ⏱️ 3-4 hours
1. ✅ Create `schemas/topology.py` - Data models
2. ✅ Create `services/topology_builder_service.py` - Core logic
3. ✅ Implement CDP topology builder
4. ✅ Implement routing topology builder
5. ✅ Create `api/topology.py` - REST endpoints
6. ✅ Register router in main.py
7. ✅ Test with existing cache data

### **Step 2: Frontend Integration** ⏱️ 2-3 hours
1. ✅ Create `TopologyBuilderModal.vue` - UI for topology options
2. ✅ Add API client functions for topology endpoints
3. ✅ Integrate "Build Topology" button in NOCCanvas toolbar
4. ✅ Implement import topology → canvas shapes/connections
5. ✅ Test end-to-end workflow

### **Step 3: Polish & Features** ⏱️ 2-3 hours
1. ✅ Add auto-layout algorithm
2. ✅ Add topology statistics endpoint
3. ✅ Add link type filtering in UI
4. ✅ Add topology preview component
5. ✅ Error handling & validation

### **Step 4: Advanced (Optional)** ⏱️ 3-5 hours
1. ⏸ Path finding algorithms
2. ⏸ Topology diff/comparison
3. ⏸ Topology snapshots
4. ⏸ Export to GraphML/DOT

---

## Data Flow Example

```
User clicks "Build Topology"
  ↓
Frontend: TopologyBuilderModal opens
  ↓
User selects: [Device1, Device2], CDP + Routing (OSPF)
  ↓
Frontend: GET /api/topology/build?device_ids=...&include_cdp=true&include_routing=true&route_types=ospf
  ↓
Backend: TopologyBuilderService.build_topology_from_cache()
  ├─ Query CDPNeighborCache for Device1, Device2
  ├─ Resolve neighbor_name → device_id via DeviceCache
  ├─ Query OSPFRouteCache for Device1, Device2
  ├─ Resolve nexthop_ip → device_id via IPAddressCache
  ├─ Deduplicate bidirectional links
  ├─ Calculate auto-layout positions
  └─ Return TopologyGraph {nodes: [...], links: [...]}
  ↓
Frontend: Display topology preview in modal
  ↓
User clicks "Import to Canvas"
  ↓
Frontend: NOCCanvas creates shapes from nodes, connections from links
  ↓
Topology visualized on canvas! 🎉
```

---

## Testing Strategy

### Backend Testing
1. **Unit Tests** - Test individual service methods
   - `_resolve_neighbor_device_id()` with various inputs
   - `_extract_cdp_links()` with mock data
   - `_deduplicate_links()` logic

2. **Integration Tests** - Test with real database
   - Build topology from seeded cache data
   - Verify node/link counts
   - Test filtering options

3. **API Tests** - Test endpoints
   - `/api/topology/build` with various parameters
   - Error handling for missing devices
   - Response schema validation

### Frontend Testing
1. **Component Tests**
   - TopologyBuilderModal interaction
   - Device selection
   - Option toggles

2. **E2E Tests**
   - Full workflow: build → preview → import
   - Verify shapes/connections created on canvas
   - Test with different topology types

---

## Performance Considerations

1. **Database Queries**
   - Use indexed fields (device_id, neighbor_ip, nexthop_ip)
   - Batch queries with `IN` clauses
   - Consider caching frequently accessed data

2. **Graph Processing**
   - Limit recursion depth for large networks
   - Implement pagination for massive topologies
   - Use efficient deduplication algorithms

3. **Frontend Rendering**
   - Lazy load topology preview for large graphs
   - Virtualize node lists
   - Debounce layout calculations

---

## Known Limitations & Future Improvements

### Current Limitations
- Requires devices to be cached first
- CDP neighbor name/IP must match exactly
- No support for LLDP (uses CDP cache table)
- Auto-layout may not respect physical topology

### Future Improvements
- Live topology updates (WebSocket)
- Custom layout algorithms (ring, hierarchical, geographic)
- Topology health monitoring (link status, errors)
- Integration with network monitoring (traffic, bandwidth)
- Multi-vendor support (more neighbor protocols)
- Topology versioning & rollback

---

## Success Metrics

**Phase 1 Complete When:**
- ✅ API returns valid TopologyGraph from cache data
- ✅ CDP links correctly resolve neighbor devices
- ✅ Routing links correctly map nexthop IPs
- ✅ All endpoints respond with proper schemas
- ✅ Unit tests pass

**Phase 2 Complete When:**
- ✅ User can build topology from UI
- ✅ Topology imports to canvas correctly
- ✅ Nodes positioned appropriately
- ✅ Links rendered between devices
- ✅ E2E workflow tested

**Phase 3 Complete When:**
- ✅ Auto-layout produces readable graphs
- ✅ Statistics provide meaningful insights
- ✅ Link filtering works correctly
- ✅ Preview component renders large graphs

**Phase 4 Complete When:**
- ✅ Path finding works reliably
- ✅ Topology diff detects changes
- ✅ Export formats validated
- ✅ Snapshots persist correctly
