"""
Nautobot service for handling GraphQL queries and REST API calls.
"""

import httpx
import logging
from typing import Dict, Any, Optional, Tuple, List
from ..core.config import settings
from ..core.cache import cache_service

logger = logging.getLogger(__name__)


class NautobotService:
    """Service for Nautobot API interactions."""

    def __init__(self):
        self.config_cache = None

    def _get_config(self, username: Optional[str] = None) -> Dict[str, Any]:
        """Get Nautobot configuration from database or global settings."""
        try:
            # Try to get settings from database first
            from sqlalchemy.orm import sessionmaker
            from ..core.database import engine
            from ..models.settings import AppSettings

            SessionLocal = sessionmaker(bind=engine)
            with SessionLocal() as session:
                db_settings = {}
                app_settings = session.query(AppSettings).all()
                for setting in app_settings:
                    db_settings[setting.key] = setting.value

                # Check if we have Nautobot config in database
                nautobot_url = db_settings.get("nautobot_url")
                nautobot_token = db_settings.get("nautobot_token")

                if nautobot_url and nautobot_token:
                    config = {
                        "url": nautobot_url,
                        "token": nautobot_token,
                        "timeout": int(db_settings.get("nautobot_timeout", "30")),
                        "verify_ssl": db_settings.get(
                            "nautobot_verify_tls", "true"
                        ).lower()
                        == "true",
                        "_source": "database",
                    }
                    logger.info(
                        f"Using Nautobot settings from database: {config['url']}"
                    )
                    return config

        except Exception as e:
            logger.warning(f"Failed to get Nautobot settings from database: {e}")

        # Fallback to environment/global settings
        config = {
            "url": settings.nautobot_url,
            "token": settings.nautobot_token,
            "timeout": settings.nautobot_timeout,
            "verify_ssl": settings.nautobot_verify_ssl,
            "_source": "environment",
        }
        logger.info(f"Using Nautobot settings from environment: {config['url']}")
        return config

    async def graphql_query(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        username: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute GraphQL query against Nautobot."""
        config = self._get_config(username)

        if not config["url"] or not config["token"]:
            raise Exception("Nautobot URL and token must be configured")

        graphql_url = f"{config['url'].rstrip('/')}/api/graphql/"

        headers = {
            "Authorization": f"Token {config['token']}",
            "Content-Type": "application/json",
        }

        payload = {"query": query, "variables": variables or {}}

        try:
            async with httpx.AsyncClient(verify=config["verify_ssl"]) as client:
                response = await client.post(
                    graphql_url,
                    json=payload,
                    headers=headers,
                    timeout=config["timeout"],
                )

                if response.status_code == 200:
                    response_data = response.json()
                    return response_data
                else:
                    logger.error(
                        f"GraphQL request failed: {response.status_code} - {response.text}"
                    )
                    raise Exception(
                        f"GraphQL request failed with status {response.status_code}: {response.text}"
                    )
        except httpx.TimeoutException:
            raise Exception(
                f"GraphQL request timed out after {config['timeout']} seconds"
            )
        except Exception as e:
            logger.error(f"GraphQL query failed: {str(e)}")
            raise

    async def rest_request(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict] = None,
        username: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute REST API request against Nautobot."""
        config = self._get_config(username)

        if not config["url"] or not config["token"]:
            raise Exception("Nautobot URL and token must be configured")

        api_url = f"{config['url'].rstrip('/')}/api/{endpoint.lstrip('/')}"

        headers = {
            "Authorization": f"Token {config['token']}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(verify=config["verify_ssl"]) as client:
                if method.upper() == "GET":
                    response = await client.get(
                        api_url,
                        headers=headers,
                        timeout=config["timeout"],
                    )
                elif method.upper() == "POST":
                    response = await client.post(
                        api_url,
                        json=data,
                        headers=headers,
                        timeout=config["timeout"],
                    )
                else:
                    raise Exception(f"Unsupported HTTP method: {method}")

                if response.status_code in [200, 201]:
                    return response.json()
                else:
                    raise Exception(
                        f"REST request failed with status {response.status_code}: {response.text}"
                    )
        except httpx.TimeoutException:
            raise Exception(f"REST request timed out after {config['timeout']} seconds")
        except Exception as e:
            logger.error(f"REST request failed: {str(e)}")
            raise

    async def test_connection(
        self, url: str, token: str, timeout: int = 30, verify_ssl: bool = True
    ) -> Tuple[bool, str]:
        """Test connection to Nautobot server."""
        try:
            graphql_url = f"{url.rstrip('/')}/api/graphql/"
            headers = {
                "Authorization": f"Token {token}",
                "Content-Type": "application/json",
            }

            # Simple query to test connection
            query = """
            query {
                devices(limit: 1) {
                    id
                }
            }
            """

            payload = {"query": query}

            async with httpx.AsyncClient(verify=verify_ssl) as client:
                response = await client.post(
                    graphql_url,
                    json=payload,
                    headers=headers,
                    timeout=timeout,
                )

                if response.status_code == 200:
                    result = response.json()
                    if "errors" in result:
                        return False, f"GraphQL errors: {result['errors']}"
                    return True, "Connection successful!"
                elif response.status_code == 401:
                    return False, "Authentication failed. Please check your token."
                elif response.status_code == 404:
                    return False, "Nautobot API not found. Please verify the URL."
                else:
                    return (
                        False,
                        f"Connection failed with status {response.status_code}",
                    )

        except httpx.TimeoutException:
            return False, f"Connection timed out after {timeout} seconds"
        except Exception as e:
            return False, f"Connection error: {str(e)}"

    async def get_devices(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        filter_type: Optional[str] = None,
        filter_value: Optional[str] = None,
        username: Optional[str] = None,
        disable_cache: bool = False,
    ) -> Dict[str, Any]:
        """Get devices with optional filtering and pagination.

        Args:
            limit: Maximum number of devices to return
            offset: Number of devices to skip
            filter_type: Type of filter ('name', 'location', 'ip_address', 'prefix')
            filter_value: Value to filter by
            username: Username for authentication
            disable_cache: If True, bypass cache and fetch fresh data
        """

        logger.info("🚀🚀🚀 get_devices() CALLED - USING GRAPHQL VERSION 🚀🚀🚀")
        logging.debug(
            f"Fetching devices with filter_type={filter_type}, filter_value={filter_value}, limit={limit}, offset={offset} disable_cache={disable_cache}"
        )

        # Check cache first (only if cache is enabled)
        cached_result = None
        cache_key = None

        if not disable_cache:
            cache_key = cache_service.generate_key(
                "nautobot",
                "devices",
                limit=limit,
                offset=offset,
                filter_type=filter_type,
                filter_value=filter_value,
            )

            cached_result = await cache_service.get(cache_key)
            if cached_result:
                return cached_result

        # Build GraphQL query based on filters
        variables = {}

        if filter_type and filter_value:
            if filter_type == "name":
                # Get total count for pagination
                count_query = """
                query devices_count_by_name($name_filter: [String]) {
                  devices(name__ire: $name_filter) {
                    id
                  }
                }
                """
                count_variables = {"name_filter": [filter_value]}
                count_result = await self.graphql_query(
                    count_query, count_variables, username
                )

                if "errors" in count_result:
                    raise Exception(
                        f"GraphQL errors in count query: {count_result['errors']}"
                    )

                total_count = len(count_result["data"]["devices"])

                # Get paginated data
                query = """
                query devices_by_name($name_filter: [String], $limit: Int, $offset: Int) {
                  devices(name__ire: $name_filter, limit: $limit, offset: $offset) {
                    id
                    name
                    role {
                      name
                    }
                    location {
                      name
                    }
                    primary_ip4 {
                      address
                    }
                    status {
                      name
                    }
                    device_type {
                      model
                    }
                    platform {
                      id
                      name
                      network_driver
                    }
                    cf_last_backup
                  }
                }
                """
                variables = {"name_filter": [filter_value]}

            elif filter_type == "location":
                query = """
                query devices_by_location($location_filter: [String], $limit: Int, $offset: Int) {
                  locations(name__ire: $location_filter) {
                    name
                    devices(limit: $limit, offset: $offset) {
                      id
                      name
                      role {
                        name
                      }
                      location {
                        name
                      }
                      primary_ip4 {
                        address
                      }
                      status {
                        name
                      }
                      device_type {
                        model
                      }
                      platform {
                        id
                        name
                        network_driver
                      }
                      cf_last_backup
                    }
                  }
                }
                """
                variables = {"location_filter": [filter_value]}

            elif filter_type == "ip_address":
                query = """
                query IPaddresses($address_filter: [String]) {
                  ip_addresses(address: $address_filter) {
                    id 
                    address 
                    description 
                    dns_name 
                    type
                    interfaces {
                      id
                      name
                      device {
                        id
                        name
                      }
                      description
                      enabled
                      mac_address
                      type
                      mode
                      ip_addresses {
                        address
                        role {
                          id 
                          name
                        }
                      }
                    }
                    primary_ip4_for {
                      id 
                      name 
                      role {
                        id
                        name
                      }
                      device_type {
                        id
                        model
                      }
                      platform {
                        id 
                        name
                        network_driver
                        manufacturer {
                          id
                          name
                        }
                      }
                      serial
                      status {
                        id 
                        name
                      }
                      primary_ip4 {
                        id
                        description
                        ip_version 
                        address 
                        host 
                        mask_length 
                        dns_name
                        status {
                          id 
                          name
                        }
                      }
                      location {
                        name
                      }
                    }
                  }
                }
                """
                variables = {"address_filter": [filter_value]}

            else:  # prefix filter
                query = """
                query devices_by_ip_prefix($prefix_filter: [String], $limit: Int, $offset: Int) {
                  prefixes(within_include: $prefix_filter) {
                    prefix
                    ip_addresses(limit: $limit, offset: $offset) {
                      primary_ip4_for {
                        id
                        name
                        role {
                          name
                        }
                        location {
                          name
                        }
                        primary_ip4 {
                          address
                        }
                        status {
                          name
                        }
                        device_type {
                          model
                        }
                        platform {
                          id
                          name
                          network_driver
                        }
                        cf_last_backup
                      }
                    }
                  }
                }
                """
                variables = {"prefix_filter": [filter_value]}

        else:
            # Standard query without filters
            query = """
            query all_devices($limit: Int, $offset: Int) {
              devices(limit: $limit, offset: $offset) {
                id
                name
                role {
                  name
                }
                location {
                  name
                }
                primary_ip4 {
                  address
                }
                status {
                  name
                }
                device_type {
                  model
                }
                platform {
                  id
                  name
                  network_driver
                }
                cf_last_backup
              }
            }
            """

        # Add pagination parameters
        if limit is not None:
            variables["limit"] = limit
        if offset is not None:
            variables["offset"] = offset

        result = await self.graphql_query(query, variables, username)
        logger.info("result: %s", result)
        if "errors" in result:
            raise Exception(f"GraphQL errors: {result['errors']}")

        # Debug: Log raw GraphQL response to check primary_ip4 structure
        logger.info("=" * 80)
        logger.info("DEBUG: RAW GRAPHQL RESPONSE")
        logger.info(f"Result keys: {result.get('data', {}).keys()}")
        
        if result.get('data', {}).get('devices'):
            devices_list = result['data']['devices']
            logger.info(f"Number of devices in GraphQL response: {len(devices_list)}")
            
            if devices_list:
                sample_device = devices_list[0]
                logger.info(f"Sample device FULL structure: {sample_device}")
                logger.info(f"Sample device name: {sample_device.get('name')}")
                logger.info(f"Sample device primary_ip4 RAW: {sample_device.get('primary_ip4')}")
                logger.info(f"Sample device primary_ip4 TYPE: {type(sample_device.get('primary_ip4'))}")
                
                # Check if primary_ip4 has address field
                if sample_device.get('primary_ip4'):
                    logger.info(f"primary_ip4 has 'address' key: {'address' in sample_device.get('primary_ip4')}")
                    if isinstance(sample_device.get('primary_ip4'), dict):
                        logger.info(f"primary_ip4 keys: {sample_device.get('primary_ip4').keys()}")
        logger.info("=" * 80)

        # Process results based on filter type
        devices = []
        total_count = 0

        if filter_type == "location":
            for location in result["data"]["locations"]:
                for device in location["devices"]:
                    device["location"] = {"name": location["name"]}
                    devices.append(device)
            total_count = len(devices)
        elif filter_type == "ip_address":
            # Extract devices from IP address query results
            devices_dict = {}
            device_ids_to_fetch = []
            
            logger.info(f"Processing IP address filter results...")
            
            for ip_addr in result["data"]["ip_addresses"]:
                logger.info(f"IP Address: {ip_addr.get('address')}")
                
                # Get devices from primary_ip4_for (these have full device data)
                if ip_addr.get("primary_ip4_for"):
                    logger.info(f"  Found {len(ip_addr['primary_ip4_for'])} devices in primary_ip4_for")
                    for device in ip_addr["primary_ip4_for"]:
                        devices_dict[device["id"]] = device
                        
                # Get devices from interfaces (these only have id and name)
                if ip_addr.get("interfaces"):
                    logger.info(f"  Found {len(ip_addr['interfaces'])} interfaces")
                    for interface in ip_addr["interfaces"]:
                        if interface.get("device"):
                            device_basic = interface["device"]
                            logger.info(f"    Interface {interface['name']} on device: {device_basic['name']} (id: {device_basic['id']})")
                            
                            # If we don't have full device data yet, mark it for fetching
                            if device_basic["id"] not in devices_dict:
                                device_ids_to_fetch.append(device_basic["id"])
            
            # Fetch full device details for devices found via interfaces
            if device_ids_to_fetch:
                logger.info(f"Fetching full details for {len(device_ids_to_fetch)} devices found via interfaces...")
                for device_id in device_ids_to_fetch:
                    try:
                        # Fetch full device data using the existing get_device method
                        full_device = await self.get_device(device_id, username)
                        if full_device:
                            devices_dict[device_id] = full_device
                            logger.info(f"  Fetched full data for device: {full_device.get('name')}")
                    except Exception as e:
                        logger.error(f"  Failed to fetch device {device_id}: {e}")
            
            devices = list(devices_dict.values())
            total_count = len(devices)
            logger.info(f"Total devices after processing ip_address filter: {total_count}")
        elif filter_type == "prefix":
            devices_dict = {}
            for prefix in result["data"]["prefixes"]:
                for ip_addr in prefix["ip_addresses"]:
                    if ip_addr["primary_ip4_for"]:
                        device = ip_addr["primary_ip4_for"]
                        devices_dict[device["id"]] = device
            devices = list(devices_dict.values())
            total_count = len(devices)
        else:
            devices = result["data"]["devices"]
            if filter_type == "name":
                total_count = total_count  # Already calculated above
            else:
                # Get total count for unfiltered results if paginated
                if limit is not None:
                    count_query = """
                    query all_devices_count {
                      devices {
                        id
                      }
                    }
                    """
                    count_result = await self.graphql_query(count_query, {}, username)
                    total_count = len(count_result["data"]["devices"])
                else:
                    total_count = len(devices)

        # Calculate pagination info
        has_more = (offset or 0) + len(devices) < total_count if limit else False

        # Debug: Log final devices data before returning
        logger.info("=" * 80)
        logger.info("DEBUG: FINAL DEVICES DATA BEFORE RETURN")
        logger.info(f"Total devices being returned: {len(devices)}")
        
        # Count devices with/without primary_ip4
        devices_with_ip = sum(1 for d in devices if d.get('primary_ip4'))
        devices_without_ip = len(devices) - devices_with_ip
        logger.info(f"Devices WITH primary_ip4: {devices_with_ip}")
        logger.info(f"Devices WITHOUT primary_ip4: {devices_without_ip}")
        
        if devices:
            sample_final = devices[0]
            logger.info(f"Sample final device name: {sample_final.get('name')}")
            logger.info(f"Sample final device FULL: {sample_final}")
            logger.info(f"Sample final device primary_ip4: {sample_final.get('primary_ip4')}")
            
            if sample_final.get('primary_ip4'):
                logger.info(f"Sample final primary_ip4 TYPE: {type(sample_final.get('primary_ip4'))}")
                if isinstance(sample_final.get('primary_ip4'), dict):
                    logger.info(f"Sample final primary_ip4 keys: {sample_final.get('primary_ip4').keys()}")
        logger.info("=" * 80)

        response_data = {
            "devices": devices,
            "count": total_count,
            "has_more": has_more,
            "is_paginated": limit is not None,
            "current_offset": offset or 0,
            "current_limit": limit,
            "next": None,
            "previous": None,
        }

        # Cache the result (only if cache is enabled)
        if not disable_cache and cache_key:
            await cache_service.set(cache_key, response_data)

        return response_data

    async def get_device(
        self, device_id: str, username: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get specific device details."""
        cache_key = cache_service.generate_key(
            "nautobot", "device", device_id=device_id
        )

        cached_device = await cache_service.get(cache_key)
        if cached_device:
            logger.debug(f"Cache hit for device: {device_id}")
            return cached_device

        query = """
        query getDevice($deviceId: ID!) {
          device(id: $deviceId) {
            id
            name
            role {
              name
            }
            location {
              name
            }
            primary_ip4 {
              address
            }
            status {
              name
            }
            device_type {
              model
            }
            platform {
              id
              name
              network_driver
            }
            cf_last_backup
          }
        }
        """

        variables = {"deviceId": device_id}
        result = await self.graphql_query(query, variables, username)

        if "errors" in result:
            raise Exception(f"GraphQL errors: {result['errors']}")

        device = result["data"]["device"]

        # Cache the device
        if device:
            await cache_service.set(cache_key, device)

        return device

    async def get_locations(
        self, username: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get list of locations."""
        cache_key = cache_service.generate_key("nautobot", "locations")

        cached_locations = await cache_service.get(cache_key)
        if cached_locations:
            return cached_locations

        query = """
        query locations {
          locations {
            id
            name
            description
            parent {
              id
              name
              description
            }
            children {
              id
              name
              description
            }
          }
        }
        """

        result = await self.graphql_query(query, username=username)

        if "errors" in result:
            raise Exception(f"GraphQL errors: {result['errors']}")

        locations = result["data"]["locations"]
        await cache_service.set(cache_key, locations)

        return locations

    async def get_stats(self, username: Optional[str] = None) -> Dict[str, Any]:
        """Get Nautobot statistics."""
        cache_key = cache_service.generate_key("nautobot", "stats")

        cached_stats = await cache_service.get(cache_key)
        if cached_stats:
            return cached_stats

        try:
            # Get device, location, and device type counts
            devices_result = await self.rest_request("dcim/devices/", username=username)
            locations_result = await self.rest_request(
                "dcim/locations/", username=username
            )
            device_types_result = await self.rest_request(
                "dcim/device-types/", username=username
            )

            # Try to get IP addresses and prefixes (might not exist in all versions)
            try:
                ip_addresses_result = await self.rest_request(
                    "ipam/ip-addresses/", username=username
                )
                ip_addresses_count = ip_addresses_result.get("count", 0)
            except Exception:
                ip_addresses_count = 0

            try:
                prefixes_result = await self.rest_request(
                    "ipam/prefixes/", username=username
                )
                prefixes_count = prefixes_result.get("count", 0)
            except Exception:
                prefixes_count = 0

            from datetime import datetime, timezone

            stats = {
                "devices": devices_result.get("count", 0),
                "locations": locations_result.get("count", 0),
                "device_types": device_types_result.get("count", 0),
                "ip_addresses": ip_addresses_count,
                "prefixes": prefixes_count,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                # Backward compatibility
                "total_devices": devices_result.get("count", 0),
                "total_locations": locations_result.get("count", 0),
                "total_device_types": device_types_result.get("count", 0),
            }

            await cache_service.set(cache_key, stats, ttl=300)  # Cache for 5 minutes
            return stats

        except Exception as e:
            logger.error(f"Error fetching Nautobot stats: {str(e)}")
            raise

    async def check_ip_address(
        self, ip_address: str, username: Optional[str] = None
    ) -> Dict[str, Any]:
        """Check if IP address is available."""
        query = """
        query device($ip_address: [String]) {
          ip_addresses(address: $ip_address) {
            primary_ip4_for {
              name
            }
          }
        }
        """

        variables = {"ip_address": [ip_address]}
        result = await self.graphql_query(query, variables, username)

        if "errors" in result:
            raise Exception(f"GraphQL errors: {result['errors']}")

        ip_addresses = result["data"]["ip_addresses"]
        exists = len(ip_addresses) > 0
        is_available = not exists

        # Check if any IP address is assigned to a device
        assigned_devices = []
        for ip in ip_addresses:
            if ip.get("primary_ip4_for"):
                for device in ip["primary_ip4_for"]:
                    assigned_devices.append({"name": device["name"]})

        is_assigned_to_device = len(assigned_devices) > 0

        return {
            "ip_address": ip_address,
            "is_available": is_available,
            "exists": exists,
            "is_assigned_to_device": is_assigned_to_device,
            "assigned_devices": assigned_devices,
            "existing_records": ip_addresses,
            "details": ip_addresses,  # Backward compatibility
        }


# Global service instance
nautobot_service = NautobotService()
