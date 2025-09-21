"""
CheckMK service for API interactions.
"""

import logging
from typing import Tuple, Dict, Any, Optional, List
from urllib.parse import urlparse
from ..core.config import settings
from ..core.cache import cache_service
from .checkmk_client import CheckMKClient, CheckMKAPIError

logger = logging.getLogger(__name__)


class CheckMKService:
    """Service for CheckMK API interactions."""

    def __init__(self):
        self.config_cache = None

    def _get_config(self) -> Dict[str, Any]:
        """Get CheckMK configuration from settings."""
        config = {
            "url": settings.checkmk_url,
            "site": settings.checkmk_site,
            "username": settings.checkmk_username,
            "password": settings.checkmk_password,
            "timeout": settings.checkmk_timeout,
            "verify_ssl": settings.checkmk_verify_ssl,
            "_source": "environment",
        }
        logger.debug(f"Using CheckMK settings: {config['url']}")
        return config

    def _get_client(self, site_name: Optional[str] = None) -> CheckMKClient:
        """Get CheckMK client instance."""
        config = self._get_config()

        if not all(config.get(key) for key in ["url", "site", "username", "password"]):
            raise Exception(
                "CheckMK settings not configured. Please configure all required settings."
            )

        # Parse URL
        url = config["url"].rstrip("/")
        if url.startswith(("http://", "https://")):
            parsed_url = urlparse(url)
            protocol = parsed_url.scheme
            host = parsed_url.netloc
        else:
            protocol = "https"
            host = url

        # Use provided site_name or configured site
        effective_site = site_name or config["site"]

        logger.info(
            f"Initializing CheckMK client for {protocol}://{host}/{effective_site}"
        )

        return CheckMKClient(
            host=host,
            site_name=effective_site,
            username=config["username"],
            password=config["password"],
            protocol=protocol,
            verify_ssl=config["verify_ssl"],
            timeout=config["timeout"],
        )

    async def test_connection(
        self, url: str, site: str, username: str, password: str, verify_ssl: bool = True
    ) -> Tuple[bool, str]:
        """Test connection to CheckMK server."""
        try:
            # Clean up URL to get host and protocol
            url = url.rstrip("/")
            if url.startswith(("http://", "https://")):
                parsed_url = urlparse(url)
                protocol = parsed_url.scheme
                host = parsed_url.netloc
            else:
                protocol = "https"
                host = url

            logger.info(f"Testing CheckMK connection to: {protocol}://{host}/{site}")

            # Create CheckMK client
            client = CheckMKClient(
                host=host,
                site_name=site,
                username=username,
                password=password,
                protocol=protocol,
                verify_ssl=verify_ssl,
                timeout=10,
            )

            # Test connection using the client
            if client.test_connection():
                try:
                    # Get version information
                    version_info = await client.get_version()
                    version = version_info.get("versions", {}).get("checkmk", "Unknown")
                    logger.info(f"CheckMK connection successful, version: {version}")
                    return True, f"Connection successful! CheckMK version: {version}"
                except CheckMKAPIError:
                    # Connection works but couldn't get version info
                    logger.info(
                        "CheckMK connection successful (could not retrieve version)"
                    )
                    return True, "Connection successful!"
            else:
                logger.warning("CheckMK connection test returned False")
                return (
                    False,
                    "Connection test failed. Please check your credentials and server configuration.",
                )

        except CheckMKAPIError as e:
            logger.error(f"CheckMK API error: {e}")
            if e.status_code == 401:
                return (
                    False,
                    "Authentication failed. Please check your username and password.",
                )
            elif e.status_code == 404:
                return (
                    False,
                    "CheckMK API not found. Please verify the server URL, site name, and that CheckMK is properly installed.",
                )
            else:
                return False, f"API error (HTTP {e.status_code}): {str(e)}"
        except Exception as e:
            logger.error(f"CheckMK connection test failed: {str(e)}")
            return (
                False,
                f"Connection failed: {str(e)}",
            )

    async def get_stats(self) -> Dict[str, Any]:
        """Get CheckMK statistics."""
        cache_key = cache_service.generate_key("checkmk", "stats")

        cached_stats = await cache_service.get(cache_key)
        if cached_stats:
            return cached_stats

        try:
            client = self._get_client()

            # Get all hosts and count them
            hosts_data = await client.get_all_hosts()
            host_count = len(hosts_data.get("value", []))

            logger.info(f"Retrieved {host_count} hosts from CheckMK")

            from datetime import datetime, timezone

            stats = {
                "total_hosts": host_count,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            await cache_service.set(cache_key, stats, ttl=300)  # Cache for 5 minutes
            return stats

        except Exception as e:
            logger.error(f"Error fetching CheckMK stats: {str(e)}")
            raise

    async def get_version(self) -> Dict[str, Any]:
        """Get CheckMK version information."""
        try:
            client = self._get_client()
            return await client.get_version()
        except Exception as e:
            logger.error(f"Error getting CheckMK version: {str(e)}")
            raise

    # Host Management

    async def get_all_hosts(
        self,
        effective_attributes: bool = False,
        include_links: bool = False,
        site: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get all hosts from CheckMK."""
        cache_key = cache_service.generate_key(
            "checkmk",
            "hosts",
            effective_attributes=effective_attributes,
            include_links=include_links,
            site=site,
        )

        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return cached_result

        try:
            client = self._get_client()
            result = await client.get_all_hosts(
                effective_attributes=effective_attributes,
                include_links=include_links,
                site=site,
            )

            await cache_service.set(cache_key, result)
            return result
        except Exception as e:
            logger.error(f"Error getting hosts: {str(e)}")
            raise

    async def get_host(
        self, hostname: str, effective_attributes: bool = False
    ) -> Dict[str, Any]:
        """Get specific host configuration."""
        cache_key = cache_service.generate_key(
            "checkmk",
            "host",
            hostname=hostname,
            effective_attributes=effective_attributes,
        )

        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return cached_result

        try:
            client = self._get_client()
            result = await client.get_host(hostname, effective_attributes)

            await cache_service.set(cache_key, result)
            return result
        except Exception as e:
            logger.error(f"Error getting host {hostname}: {str(e)}")
            raise

    async def create_host(
        self,
        hostname: str,
        folder: str = "/",
        attributes: Optional[Dict[str, Any]] = None,
        bake_agent: bool = False,
    ) -> Dict[str, Any]:
        """Create new host in CheckMK."""
        try:
            client = self._get_client()
            result = await client.create_host(
                hostname=hostname,
                folder=folder,
                attributes=attributes or {},
                bake_agent=bake_agent,
            )

            # Clear cache
            await cache_service.clear_pattern("checkmk:hosts*")

            return result
        except Exception as e:
            logger.error(f"Error creating host {hostname}: {str(e)}")
            raise

    async def update_host(
        self, hostname: str, attributes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update existing host configuration."""
        try:
            client = self._get_client()
            result = await client.update_host(hostname, attributes)

            # Clear cache
            await cache_service.clear_pattern(f"checkmk:host:hostname:{hostname}*")
            await cache_service.clear_pattern("checkmk:hosts*")

            return result
        except Exception as e:
            logger.error(f"Error updating host {hostname}: {str(e)}")
            raise

    async def delete_host(self, hostname: str) -> None:
        """Delete host from CheckMK."""
        try:
            client = self._get_client()
            await client.delete_host(hostname)

            # Clear cache
            await cache_service.clear_pattern(f"checkmk:host:hostname:{hostname}*")
            await cache_service.clear_pattern("checkmk:hosts*")

        except Exception as e:
            logger.error(f"Error deleting host {hostname}: {str(e)}")
            raise

    async def move_host(self, hostname: str, target_folder: str) -> Dict[str, Any]:
        """Move host to different folder."""
        try:
            client = self._get_client()
            # Convert folder path format: CheckMK uses ~ instead of /
            normalized_folder = (
                target_folder.replace("//", "/") if target_folder else "/"
            )
            checkmk_folder = (
                normalized_folder.replace("/", "~") if normalized_folder else "~"
            )

            result = await client.move_host(hostname, checkmk_folder)

            # Clear cache
            await cache_service.clear_pattern(f"checkmk:host:hostname:{hostname}*")
            await cache_service.clear_pattern("checkmk:hosts*")
            await cache_service.clear_pattern("checkmk:folders*")

            return result
        except Exception as e:
            logger.error(f"Error moving host {hostname}: {str(e)}")
            raise

    async def rename_host(self, hostname: str, new_name: str) -> Dict[str, Any]:
        """Rename host."""
        try:
            client = self._get_client()
            result = await client.rename_host(hostname, new_name)

            # Clear cache
            await cache_service.clear_pattern(f"checkmk:host:hostname:{hostname}*")
            await cache_service.clear_pattern(f"checkmk:host:hostname:{new_name}*")
            await cache_service.clear_pattern("checkmk:hosts*")

            return result
        except Exception as e:
            logger.error(f"Error renaming host {hostname}: {str(e)}")
            raise

    # Bulk Operations

    async def bulk_create_hosts(self, hosts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create multiple hosts in one request."""
        try:
            client = self._get_client()
            result = await client.bulk_create_hosts(hosts)

            # Clear cache
            await cache_service.clear_pattern("checkmk:hosts*")

            return result
        except Exception as e:
            logger.error(f"Error bulk creating hosts: {str(e)}")
            raise

    async def bulk_update_hosts(
        self, hosts: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Update multiple hosts in one request."""
        try:
            client = self._get_client()
            result = await client.bulk_update_hosts(hosts)

            # Clear cache
            await cache_service.clear_pattern("checkmk:host*")
            await cache_service.clear_pattern("checkmk:hosts*")

            return result
        except Exception as e:
            logger.error(f"Error bulk updating hosts: {str(e)}")
            raise

    async def bulk_delete_hosts(self, hostnames: List[str]) -> Dict[str, Any]:
        """Delete multiple hosts in one request."""
        try:
            client = self._get_client()
            result = await client.bulk_delete_hosts(hostnames)

            # Clear cache
            await cache_service.clear_pattern("checkmk:host*")
            await cache_service.clear_pattern("checkmk:hosts*")

            return result
        except Exception as e:
            logger.error(f"Error bulk deleting hosts: {str(e)}")
            raise

    # Monitoring

    async def get_all_monitored_hosts(
        self,
        columns: Optional[List[str]] = None,
        query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get all monitored hosts with status information."""
        try:
            client = self._get_client()
            return await client.get_all_monitored_hosts(columns=columns, query=query)
        except Exception as e:
            logger.error(f"Error getting monitored hosts: {str(e)}")
            raise

    async def get_monitored_host(
        self,
        hostname: str,
        columns: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get monitored host with status information."""
        try:
            client = self._get_client()
            return await client.get_monitored_host(hostname, columns=columns)
        except Exception as e:
            logger.error(f"Error getting monitored host {hostname}: {str(e)}")
            raise

    async def get_host_services(
        self,
        hostname: str,
        columns: Optional[List[str]] = None,
        query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get services for a specific host."""
        try:
            client = self._get_client()
            return await client.get_host_services(
                hostname, columns=columns, query=query
            )
        except Exception as e:
            logger.error(f"Error getting services for host {hostname}: {str(e)}")
            raise

    # Service Discovery

    async def get_service_discovery(self, hostname: str) -> Dict[str, Any]:
        """Get service discovery status for a host."""
        try:
            client = self._get_client()
            return await client.get_service_discovery(hostname)
        except Exception as e:
            logger.error(
                f"Error getting service discovery for host {hostname}: {str(e)}"
            )
            raise

    async def start_service_discovery(
        self, hostname: str, mode: str = "new"
    ) -> Dict[str, Any]:
        """Start service discovery for a host."""
        try:
            client = self._get_client()
            return await client.start_service_discovery(hostname, mode)
        except Exception as e:
            logger.error(
                f"Error starting service discovery for host {hostname}: {str(e)}"
            )
            raise

    # Configuration Management

    async def get_pending_changes(self) -> Dict[str, Any]:
        """Get pending configuration changes."""
        try:
            client = self._get_client()
            return await client.get_pending_changes()
        except Exception as e:
            logger.error(f"Error getting pending changes: {str(e)}")
            raise

    async def activate_changes(
        self,
        sites: Optional[List[str]] = None,
        force_foreign_changes: bool = False,
        redirect: bool = False,
    ) -> Dict[str, Any]:
        """Activate pending configuration changes."""
        try:
            client = self._get_client()
            result = await client.activate_changes(
                sites=sites,
                force_foreign_changes=force_foreign_changes,
                redirect=redirect,
            )

            # Clear all cache after activation
            await cache_service.clear_pattern("checkmk:*")

            return result
        except Exception as e:
            logger.error(f"Error activating changes: {str(e)}")
            raise

    # Folders

    async def get_all_folders(
        self,
        parent: Optional[str] = None,
        recursive: bool = False,
        show_hosts: bool = False,
    ) -> Dict[str, Any]:
        """Get all folders."""
        cache_key = cache_service.generate_key(
            "checkmk",
            "folders",
            parent=parent,
            recursive=recursive,
            show_hosts=show_hosts,
        )

        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return cached_result

        try:
            client = self._get_client()
            result = await client.get_all_folders(
                parent=parent,
                recursive=recursive,
                show_hosts=show_hosts,
            )

            await cache_service.set(cache_key, result)
            return result
        except Exception as e:
            logger.error(f"Error getting folders: {str(e)}")
            raise

    async def get_folder(
        self, folder_path: str, show_hosts: bool = False
    ) -> Dict[str, Any]:
        """Get specific folder."""
        try:
            client = self._get_client()
            # Convert folder path format: CheckMK uses ~ instead of /
            normalized_folder_path = (
                folder_path.replace("//", "/") if folder_path else "/"
            )
            checkmk_folder_path = (
                normalized_folder_path.replace("/", "~")
                if normalized_folder_path
                else "~"
            )
            return await client.get_folder(checkmk_folder_path, show_hosts=show_hosts)
        except Exception as e:
            logger.error(f"Error getting folder {folder_path}: {str(e)}")
            raise

    async def create_folder(
        self,
        name: str,
        title: str,
        parent: str = "/",
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create new folder."""
        try:
            client = self._get_client()
            # Convert folder path format
            normalized_parent = parent.replace("//", "/") if parent else "/"
            checkmk_parent = (
                normalized_parent.replace("/", "~") if normalized_parent else "~"
            )

            result = await client.create_folder(
                name=name,
                title=title,
                parent=checkmk_parent,
                attributes=attributes or {},
            )

            # Clear cache
            await cache_service.clear_pattern("checkmk:folders*")

            return result
        except Exception as e:
            logger.error(f"Error creating folder {name}: {str(e)}")
            raise


# Global service instance
checkmk_service = CheckMKService()
