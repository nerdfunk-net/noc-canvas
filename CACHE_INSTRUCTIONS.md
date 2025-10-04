# Device Cache System - Instructions

## Overview

The Device Cache System is a PostgreSQL-based caching layer for storing network device discovery data. It caches information about devices, interfaces, IP addresses, and ARP tables to reduce the need for repeated queries to network devices and improve application performance.

## Cache Structure

### Database Tables

The cache consists of four main tables with hierarchical relationships:

```
DeviceCache (root)
├── InterfaceCache (1:N)
│   └── IPAddressCache (1:N)
├── IPAddressCache (1:N)
└── ARPCache (1:N)
```

#### 1. DeviceCache
Stores basic device information and cache metadata.

**Fields:**
- `device_id` (Primary Key) - Nautobot device UUID
- `device_name` - Device hostname/name
- `primary_ip` - Primary management IP address
- `platform` - Device platform (e.g., "IOS", "IOS XE", "Nexus")
- `last_updated` - Timestamp of last cache update
- `cache_valid_until` - Expiration timestamp for cache entry
- `polling_enabled` - Whether this device should be polled

**Relationships:**
- Has many Interfaces
- Has many IP Addresses
- Has many ARP Entries

#### 2. InterfaceCache
Stores interface details including MAC addresses and status.

**Fields:**
- `id` (Primary Key, Auto-increment)
- `device_id` (Foreign Key → DeviceCache)
- `interface_name` - Interface name (e.g., "GigabitEthernet0/1")
- `mac_address` - Interface MAC address (indexed for lookups)
- `status` - Interface status ("up", "down", "admin-down")
- `description` - Interface description
- `speed` - Interface speed
- `duplex` - Duplex setting
- `vlan_id` - VLAN ID
- `last_updated` - Timestamp of last update

**Indexes:**
- Unique index on (device_id, interface_name)
- Index on mac_address for reverse MAC lookups

#### 3. IPAddressCache
Stores IP addresses assigned to interfaces.

**Fields:**
- `id` (Primary Key, Auto-increment)
- `device_id` (Foreign Key → DeviceCache)
- `interface_id` (Foreign Key → InterfaceCache)
- `interface_name` - Denormalized for easier queries
- `ip_address` - IP address (indexed)
- `subnet_mask` - Subnet mask
- `ip_version` - 4 or 6
- `is_primary` - Whether this is the primary IP
- `last_updated` - Timestamp of last update

**Indexes:**
- Index on ip_address for "which device has this IP" queries
- Index on (device_id, interface_name)

#### 4. ARPCache
Stores ARP entries from devices.

**Fields:**
- `id` (Primary Key, Auto-increment)
- `device_id` (Foreign Key → DeviceCache)
- `ip_address` - ARP IP address (indexed)
- `mac_address` - ARP MAC address (indexed)
- `interface_name` - Interface where ARP was learned
- `age` - ARP entry age
- `arp_type` - ARP type (e.g., "ARPA")
- `last_updated` - Timestamp of last update

**Indexes:**
- Index on ip_address
- Index on mac_address for MAC lookups
- Index on (device_id, ip_address)

## Cache TTL (Time-To-Live)

Cache entries have a configurable TTL that determines how long data is considered valid:

- Default TTL: 60 minutes (configurable in Settings → Cache)
- Each cache entry has a `cache_valid_until` timestamp
- Expired entries can be cleaned manually or automatically
- Valid vs expired status is shown in statistics

## API Endpoints

All cache endpoints are prefixed with `/api/cache`.

### Statistics & Monitoring

#### `GET /api/cache/statistics`
Get comprehensive cache statistics including:
- Total counts (devices, interfaces, IPs, ARP entries)
- Cache validity status (valid/expired percentages)
- Polling status (enabled/disabled counts)
- Recently updated devices (top 5)
- Devices with most interfaces (top 5)

**Response:**
```json
{
  "total": {
    "devices": 150,
    "interfaces": 2340,
    "ip_addresses": 3120,
    "arp_entries": 5678
  },
  "cache_status": {
    "valid": 145,
    "expired": 5,
    "valid_percentage": 96.7
  },
  "polling": {
    "enabled": 140,
    "disabled": 10
  },
  "recent_updates": [...],
  "top_devices": [...]
}
```

### Device Operations

#### `GET /api/cache/devices`
Get all cached devices with pagination and filtering.

**Query Parameters:**
- `skip` - Offset for pagination (default: 0)
- `limit` - Number of results (default: 100, max: 1000)
- `polling_enabled` - Filter by polling status (true/false)

**Example:**
```bash
GET /api/cache/devices?limit=50&polling_enabled=true
```

#### `GET /api/cache/devices/{device_id}`
Get specific device by Nautobot UUID.

#### `GET /api/cache/devices/by-name/{device_name}`
Get device by hostname/name.

#### `GET /api/cache/devices/by-ip/{ip_address}`
Find which device(s) have a specific IP address.

**Use Case:** Determine which device owns an IP address.

#### `POST /api/cache/devices/{device_id}/bulk-update`
**Primary endpoint for populating cache after device discovery.**

Updates entire device cache including all related data in a single transaction.

**Query Parameters:**
- `cache_ttl_minutes` - TTL for this cache entry (default: 60, min: 1, max: 1440)

**Request Body:**
```json
{
  "device": {
    "device_id": "uuid-here",
    "device_name": "router-01",
    "primary_ip": "10.0.0.1",
    "platform": "IOS XE",
    "polling_enabled": true
  },
  "interfaces": [
    {
      "device_id": "uuid-here",
      "interface_name": "GigabitEthernet0/0",
      "mac_address": "00:1a:2b:3c:4d:5e",
      "status": "up",
      "description": "Uplink to core",
      "speed": "1000",
      "duplex": "full"
    }
  ],
  "ip_addresses": [
    {
      "device_id": "uuid-here",
      "interface_name": "GigabitEthernet0/0",
      "ip_address": "10.0.0.1",
      "subnet_mask": "255.255.255.0",
      "ip_version": 4,
      "is_primary": true
    }
  ],
  "arp_entries": [
    {
      "device_id": "uuid-here",
      "ip_address": "10.0.0.10",
      "mac_address": "aa:bb:cc:dd:ee:ff",
      "interface_name": "GigabitEthernet0/0",
      "age": 120,
      "arp_type": "ARPA"
    }
  ]
}
```

#### `PUT /api/cache/devices/{device_id}/polling`
Enable or disable polling for a device.

**Query Parameters:**
- `enabled` - true or false

**Example:**
```bash
PUT /api/cache/devices/uuid-123/polling?enabled=false
```

#### `DELETE /api/cache/devices/{device_id}`
Delete all cached data for a device (cascades to interfaces, IPs, ARP).

### Interface Operations

#### `GET /api/cache/interfaces/{device_id}`
Get all interfaces for a device.

#### `GET /api/cache/interfaces/{device_id}/{interface_name}`
Get specific interface details.

**Example:**
```bash
GET /api/cache/interfaces/uuid-123/GigabitEthernet0/1
```

#### `GET /api/cache/interfaces/by-mac/{mac_address}`
Find interfaces by MAC address (reverse MAC lookup).

**Use Case:** Discover which device and interface has a specific MAC address.

**Example:**
```bash
GET /api/cache/interfaces/by-mac/00:1a:2b:3c:4d:5e
```

### IP Address Operations

#### `GET /api/cache/ip-addresses/{device_id}`
Get all IP addresses for a device.

### ARP Operations

#### `GET /api/cache/arp/{device_id}`
Get all ARP entries for a device.

#### `GET /api/cache/arp/by-mac/{mac_address}`
Find ARP entries by MAC address.

**Use Case:** Track which IP addresses are associated with a MAC.

#### `GET /api/cache/arp/by-ip/{ip_address}`
Find ARP entries by IP address.

**Use Case:** See which devices have learned an IP in their ARP table.

### Cache Maintenance

#### `DELETE /api/cache/expired`
Clean all expired cache entries across all devices.

**Response:**
```json
{
  "message": "Cleaned 23 expired cache entries"
}
```

#### `DELETE /api/cache/devices/{device_id}/expired`
Clean expired cache for a specific device.

## Using the Cache Service (Backend)

### Import the Service

```python
from app.services.device_cache_service import DeviceCacheService
from app.core.database import get_db
```

### Common Operations

#### Check if Cache is Valid
```python
device = DeviceCacheService.get_device(db, device_id)
if device and DeviceCacheService.is_cache_valid(device):
    # Use cached data
    return device
else:
    # Refresh from device
    data = fetch_from_device()
    DeviceCacheService.bulk_update_device_cache(db, data)
```

#### Populate Cache After Discovery
```python
from app.schemas.device_cache import BulkCacheUpdate, DeviceCacheCreate

cache_data = BulkCacheUpdate(
    device=DeviceCacheCreate(...),
    interfaces=[...],
    ip_addresses=[...],
    arp_entries=[...]
)

DeviceCacheService.bulk_update_device_cache(
    db,
    cache_data,
    cache_ttl_minutes=60
)
```

#### Find Device by IP
```python
# Returns list of IPAddressCache entries
ip_entries = DeviceCacheService.get_devices_by_ip(db, "10.0.0.1")
for entry in ip_entries:
    device = entry.device
    print(f"IP {entry.ip_address} found on {device.device_name}")
```

#### MAC Address Lookup
```python
# Find interface by MAC
interfaces = DeviceCacheService.get_interfaces_by_mac(db, "00:1a:2b:3c:4d:5e")
for interface in interfaces:
    print(f"MAC on {interface.device.device_name} - {interface.interface_name}")

# Find ARP entries by MAC
arp_entries = DeviceCacheService.get_arp_by_mac(db, "aa:bb:cc:dd:ee:ff")
```

#### Clean Expired Cache
```python
# Clean all expired
count = DeviceCacheService.clean_expired_cache(db)
print(f"Cleaned {count} expired entries")

# Clean specific device
count = DeviceCacheService.clean_expired_cache(db, device_id="uuid-123")
```

## Using the Cache (Frontend)

The cache is accessible through the Settings page under the "Cache" tab.

### Cache Settings
Configure cache behavior:
- **Default TTL** - How long cache entries remain valid (1-1440 minutes)
- **Auto-refresh** - Enable automatic cache refresh
- **Auto-refresh Interval** - How often to refresh (5-1440 minutes)
- **Clean on Startup** - Automatically clean expired entries on app start

### View Statistics
Click "Refresh" to load:
- Total counts for devices, interfaces, IPs, and ARP entries
- Cache validity percentage
- Polling status distribution
- Recently updated devices
- Devices with most interfaces

### Browse Cache
Switch to "Devices" view to see:
- Device name
- Primary IP
- Platform
- Last updated timestamp
- Cache valid until (color-coded: green=valid, red=expired)
- Polling status

### Cache Maintenance
- **Clean Expired Cache** - Remove all expired entries
- **Save Settings** - Persist cache configuration

### API Usage from Frontend

```typescript
// Load statistics
const response = await makeAuthenticatedRequest('/api/cache/statistics')
const stats = await response.json()

// Load devices
const devicesResponse = await makeAuthenticatedRequest('/api/cache/devices?limit=100')
const devices = await devicesResponse.json()

// Clean expired cache
await makeAuthenticatedRequest('/api/cache/expired', { method: 'DELETE' })
```

## Best Practices

### 1. Cache Population
- Always use `bulk_update_device_cache` for complete device updates
- Set appropriate TTL based on data volatility:
  - Static data (interfaces, IPs): 1440 minutes (24 hours)
  - Dynamic data (ARP tables): 30-60 minutes
  - Device status: 15-30 minutes

### 2. Cache Validation
- Check `cache_valid_until` before using cached data
- Implement fallback to device query if cache is expired
- Use `is_cache_valid()` helper method

### 3. Polling Management
- Disable polling for maintenance mode devices
- Use polling filters in queries to exclude disabled devices
- Toggle polling via API when devices go offline

### 4. Performance Optimization
- Use indexed fields (MAC, IP) for lookups
- Leverage pagination for large result sets
- Use specific queries (by-name, by-ip) instead of loading all devices

### 5. Cache Maintenance
- Schedule periodic cleanup of expired entries
- Monitor cache statistics for size management
- Consider implementing auto-refresh for critical devices

### 6. Error Handling
- Handle 404 errors when cache misses occur
- Implement retry logic with cache invalidation
- Log cache failures for monitoring

## Common Use Cases

### Use Case 1: Device Discovery Flow
```python
# 1. Check cache first
device = DeviceCacheService.get_device(db, device_id)
if device and DeviceCacheService.is_cache_valid(device):
    return device.interfaces

# 2. Query device if cache miss/expired
data = query_device_interfaces(device_ip)

# 3. Update cache
cache_data = BulkCacheUpdate(...)
DeviceCacheService.bulk_update_device_cache(db, cache_data)

return data
```

### Use Case 2: IP Address Tracking
```python
# Find which device owns an IP
devices = DeviceCacheService.get_devices_by_ip(db, "10.0.0.50")
for ip_entry in devices:
    print(f"IP on {ip_entry.device.device_name} interface {ip_entry.interface_name}")
```

### Use Case 3: MAC Address Tracking
```python
# Find interface with MAC
interfaces = DeviceCacheService.get_interfaces_by_mac(db, "aa:bb:cc:dd:ee:ff")

# Find which devices have this MAC in ARP
arp_entries = DeviceCacheService.get_arp_by_mac(db, "aa:bb:cc:dd:ee:ff")

# Trace MAC across network
for arp in arp_entries:
    print(f"Device {arp.device.device_name} learned MAC on {arp.interface_name}")
```

### Use Case 4: Neighbor Discovery
```python
# 1. Get device's ARP table from cache
device = DeviceCacheService.get_device(db, device_id)
arp_entries = device.arp_entries

# 2. For each ARP entry, find which device has that IP
for arp in arp_entries:
    neighbors = DeviceCacheService.get_devices_by_ip(db, arp.ip_address)
    # Build neighbor relationships
```

## Troubleshooting

### Cache Not Updating
1. Check `polling_enabled` flag on device
2. Verify cache TTL hasn't expired
3. Check logs for bulk update errors
4. Ensure device_id matches between Nautobot and cache

### Missing Data
1. Verify relationships are properly set (device_id, interface_id)
2. Check if data was included in bulk update payload
3. Ensure cascade deletes aren't removing data unexpectedly

### Performance Issues
1. Add indexes on frequently queried fields
2. Use pagination for large datasets
3. Implement cache-first strategy with fallbacks
4. Monitor database query performance

### Stale Data
1. Reduce cache TTL for frequently changing data
2. Implement event-driven cache invalidation
3. Enable auto-refresh for critical devices
4. Schedule regular cache cleanup

## Future Enhancements

Potential improvements to consider:

1. **Routing Cache** - Cache routing tables (Phase 2)
2. **MAC Table Cache** - Cache MAC address tables (Phase 2)
3. **LLDP/CDP Cache** - Cache neighbor discovery data (Phase 2)
4. **Cache Events** - Emit events on cache updates for real-time UI updates
5. **Selective Refresh** - Refresh only changed data instead of full updates
6. **Cache Metrics** - Track hit/miss rates, query performance
7. **Background Refresh** - Automatic background polling for enabled devices
8. **Cache Versioning** - Track cache versions for change detection
