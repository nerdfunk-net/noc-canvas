"""
CheckMK REST API client for host and monitoring management.
"""

import httpx
import json
import logging
from typing import Dict, Any, Optional, List
from urllib.parse import quote

logger = logging.getLogger(__name__)


class CheckMKAPIError(Exception):
    """CheckMK API error exception."""

    def __init__(self, message: str, status_code: int = None, response_data: Dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class CheckMKClient:
    """CheckMK REST API client."""

    def __init__(
        self,
        host: str,
        site_name: str,
        username: str,
        password: str,
        protocol: str = "https",
        verify_ssl: bool = True,
        timeout: int = 30,
    ):
        self.host = host.rstrip("/")
        self.site_name = site_name
        self.username = username
        self.password = password
        self.protocol = protocol
        self.verify_ssl = verify_ssl
        self.timeout = timeout

        # Build base URL
        self.base_url = f"{protocol}://{host}/{site_name}/check_mk/api/1.0"

        # Setup authentication headers
        self.headers = {
            "Authorization": f"Bearer {username} {password}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request to CheckMK API."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            async with httpx.AsyncClient(verify=self.verify_ssl) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=data,
                    params=params,
                    timeout=self.timeout,
                )

                # Handle response
                if response.status_code in [200, 201, 204]:
                    try:
                        return response.json()
                    except json.JSONDecodeError:
                        return {"status": "success"}
                else:
                    # Try to parse error response
                    try:
                        error_data = response.json()
                    except json.JSONDecodeError:
                        error_data = {"detail": response.text}

                    raise CheckMKAPIError(
                        f"API request failed: {response.status_code}",
                        status_code=response.status_code,
                        response_data=error_data,
                    )

        except httpx.TimeoutException:
            raise CheckMKAPIError(f"Request timed out after {self.timeout} seconds")
        except httpx.RequestError as e:
            raise CheckMKAPIError(f"Request error: {str(e)}")

    def test_connection(self) -> bool:
        """Test connection to CheckMK server (synchronous)."""
        try:
            import requests

            url = f"{self.base_url}/version"
            auth = (self.username, self.password)

            response = requests.get(
                url,
                auth=auth,
                verify=self.verify_ssl,
                timeout=10,
            )

            return response.status_code == 200
        except Exception:
            return False

    async def get_version(self) -> Dict[str, Any]:
        """Get CheckMK version information."""
        return await self._request("GET", "version")

    # Host Management

    async def get_all_hosts(
        self,
        effective_attributes: bool = False,
        include_links: bool = False,
        site: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get all hosts."""
        params = {}
        if effective_attributes:
            params["effective_attributes"] = "true"
        if include_links:
            params["include_links"] = "true"
        if site:
            params["site"] = site

        return await self._request("GET", "objects/host_config", params=params)

    async def get_host(self, hostname: str, effective_attributes: bool = False) -> Dict[str, Any]:
        """Get specific host configuration."""
        params = {}
        if effective_attributes:
            params["effective_attributes"] = "true"

        endpoint = f"objects/host_config/{quote(hostname)}"
        return await self._request("GET", endpoint, params=params)

    async def create_host(
        self,
        hostname: str,
        folder: str = "/",
        attributes: Optional[Dict[str, Any]] = None,
        bake_agent: bool = False,
    ) -> Dict[str, Any]:
        """Create new host."""
        data = {
            "host_name": hostname,
            "folder": folder.replace("/", "~") if folder != "/" else "~",
            "attributes": attributes or {},
        }

        params = {}
        if bake_agent:
            params["bake_agent"] = "true"

        return await self._request("POST", "objects/host_config", data=data, params=params)

    async def update_host(self, hostname: str, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing host."""
        data = {"attributes": attributes}
        endpoint = f"objects/host_config/{quote(hostname)}"
        return await self._request("PUT", endpoint, data=data)

    async def delete_host(self, hostname: str) -> None:
        """Delete host."""
        endpoint = f"objects/host_config/{quote(hostname)}"
        await self._request("DELETE", endpoint)

    async def move_host(self, hostname: str, target_folder: str) -> Dict[str, Any]:
        """Move host to different folder."""
        data = {"target_folder": target_folder}
        endpoint = f"objects/host_config/{quote(hostname)}/actions/move"
        return await self._request("POST", endpoint, data=data)

    async def rename_host(self, hostname: str, new_name: str) -> Dict[str, Any]:
        """Rename host."""
        data = {"new_name": new_name}
        endpoint = f"objects/host_config/{quote(hostname)}/actions/rename"
        return await self._request("POST", endpoint, data=data)

    # Bulk Operations

    async def bulk_create_hosts(self, hosts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create multiple hosts."""
        data = {"entries": hosts}
        return await self._request("POST", "domain-types/host_config/actions/bulk-create", data=data)

    async def bulk_update_hosts(self, hosts: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Update multiple hosts."""
        data = {"entries": hosts}
        return await self._request("PUT", "domain-types/host_config/actions/bulk-update", data=data)

    async def bulk_delete_hosts(self, hostnames: List[str]) -> Dict[str, Any]:
        """Delete multiple hosts."""
        data = {"entries": hostnames}
        return await self._request("POST", "domain-types/host_config/actions/bulk-delete", data=data)

    # Monitoring

    async def get_all_monitored_hosts(
        self,
        columns: Optional[List[str]] = None,
        query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get all monitored hosts with status."""
        params = {}
        if columns:
            params["columns"] = columns
        if query:
            params["query"] = query

        return await self._request("GET", "domain-types/host/collections/all", params=params)

    async def get_monitored_host(
        self,
        hostname: str,
        columns: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get monitored host status."""
        params = {}
        if columns:
            params["columns"] = columns

        endpoint = f"objects/host/{quote(hostname)}"
        return await self._request("GET", endpoint, params=params)

    async def get_host_services(
        self,
        hostname: str,
        columns: Optional[List[str]] = None,
        query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get services for a host."""
        params = {"host_name": hostname}
        if columns:
            params["columns"] = columns
        if query:
            params["query"] = query

        return await self._request("GET", "domain-types/service/collections/all", params=params)

    async def show_service(
        self,
        hostname: str,
        service: str,
        columns: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Show specific service details."""
        params = {}
        if columns:
            params["columns"] = columns

        endpoint = f"objects/service/{quote(hostname)}/{quote(service)}"
        return await self._request("GET", endpoint, params=params)

    # Service Discovery

    async def get_service_discovery(self, hostname: str) -> Dict[str, Any]:
        """Get service discovery status."""
        endpoint = f"objects/host/{quote(hostname)}/actions/show_discovery"
        return await self._request("GET", endpoint)

    async def start_service_discovery(self, hostname: str, mode: str = "new") -> Dict[str, Any]:
        """Start service discovery."""
        data = {"mode": mode}
        endpoint = f"objects/host/{quote(hostname)}/actions/discover_services"
        return await self._request("POST", endpoint, data=data)

    async def wait_for_service_discovery(self, hostname: str) -> Dict[str, Any]:
        """Wait for service discovery completion."""
        endpoint = f"objects/host/{quote(hostname)}/actions/wait-for-completion"
        return await self._request("POST", endpoint)

    async def update_discovery_phase(
        self,
        hostname: str,
        phase: str,
        services: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Update discovery phase."""
        data = {"phase": phase}
        if services:
            data["services"] = services

        endpoint = f"objects/host/{quote(hostname)}/actions/update_discovery_phase"
        return await self._request("POST", endpoint, data=data)

    # Problem Management

    async def acknowledge_host_problem(
        self,
        hostname: str,
        comment: str,
        sticky: bool = True,
        persistent: bool = False,
        notify: bool = False,
    ) -> Dict[str, Any]:
        """Acknowledge host problem."""
        data = {
            "acknowledge_type": "host",
            "host_name": hostname,
            "comment": comment,
            "sticky": sticky,
            "persistent": persistent,
            "notify": notify,
        }
        return await self._request("POST", "domain-types/acknowledge/collections/host", data=data)

    async def acknowledge_service_problem(
        self,
        hostname: str,
        service_description: str,
        comment: str,
        sticky: bool = True,
        persistent: bool = False,
        notify: bool = False,
    ) -> Dict[str, Any]:
        """Acknowledge service problem."""
        data = {
            "acknowledge_type": "service",
            "host_name": hostname,
            "service_description": service_description,
            "comment": comment,
            "sticky": sticky,
            "persistent": persistent,
            "notify": notify,
        }
        return await self._request("POST", "domain-types/acknowledge/collections/service", data=data)

    async def delete_acknowledgment(self, ack_id: str) -> None:
        """Delete acknowledgment."""
        endpoint = f"objects/acknowledge/{quote(ack_id)}"
        await self._request("DELETE", endpoint)

    async def create_host_downtime(
        self,
        hostname: str,
        start_time: str,
        end_time: str,
        comment: str,
        downtime_type: str = "fixed",
    ) -> Dict[str, Any]:
        """Create host downtime."""
        data = {
            "downtime_type": downtime_type,
            "host_name": hostname,
            "start_time": start_time,
            "end_time": end_time,
            "comment": comment,
        }
        return await self._request("POST", "domain-types/downtime/collections/host", data=data)

    async def add_host_comment(
        self,
        hostname: str,
        comment: str,
        persistent: bool = False,
    ) -> Dict[str, Any]:
        """Add comment to host."""
        data = {
            "comment_type": "host",
            "host_name": hostname,
            "comment": comment,
            "persistent": persistent,
        }
        return await self._request("POST", "domain-types/comment/collections/host", data=data)

    async def add_service_comment(
        self,
        hostname: str,
        service_description: str,
        comment: str,
        persistent: bool = False,
    ) -> Dict[str, Any]:
        """Add comment to service."""
        data = {
            "comment_type": "service",
            "host_name": hostname,
            "service_description": service_description,
            "comment": comment,
            "persistent": persistent,
        }
        return await self._request("POST", "domain-types/comment/collections/service", data=data)

    # Configuration Management

    async def get_pending_changes(self) -> Dict[str, Any]:
        """Get pending configuration changes."""
        return await self._request("GET", "domain-types/activation_run/collections/pending_changes")

    async def activate_changes(
        self,
        sites: Optional[List[str]] = None,
        force_foreign_changes: bool = False,
        redirect: bool = False,
    ) -> Dict[str, Any]:
        """Activate pending changes."""
        data = {
            "force_foreign_changes": force_foreign_changes,
            "redirect": redirect,
        }
        if sites:
            data["sites"] = sites

        return await self._request("POST", "domain-types/activation_run/actions/activate-changes", data=data)

    async def get_activation_status(self, activation_id: str) -> Dict[str, Any]:
        """Get activation status."""
        endpoint = f"objects/activation_run/{quote(activation_id)}"
        return await self._request("GET", endpoint)

    async def wait_for_activation_completion(self, activation_id: str) -> Dict[str, Any]:
        """Wait for activation completion."""
        endpoint = f"objects/activation_run/{quote(activation_id)}/actions/wait-for-completion"
        return await self._request("POST", endpoint)

    async def get_running_activations(self) -> Dict[str, Any]:
        """Get running activations."""
        return await self._request("GET", "domain-types/activation_run/collections/running")

    # Folders

    async def get_all_folders(
        self,
        parent: Optional[str] = None,
        recursive: bool = False,
        show_hosts: bool = False,
    ) -> Dict[str, Any]:
        """Get all folders."""
        params = {}
        if parent:
            params["parent"] = parent.replace("/", "~") if parent != "/" else "~"
        if recursive:
            params["recursive"] = "true"
        if show_hosts:
            params["show_hosts"] = "true"

        return await self._request("GET", "objects/folder_config", params=params)

    async def get_folder(self, folder_path: str, show_hosts: bool = False) -> Dict[str, Any]:
        """Get specific folder."""
        params = {}
        if show_hosts:
            params["show_hosts"] = "true"

        endpoint = f"objects/folder_config/{quote(folder_path)}"
        return await self._request("GET", endpoint, params=params)

    async def create_folder(
        self,
        name: str,
        title: str,
        parent: str = "/",
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create new folder."""
        data = {
            "name": name,
            "title": title,
            "parent": parent,
            "attributes": attributes or {},
        }
        return await self._request("POST", "objects/folder_config", data=data)

    async def update_folder(
        self,
        folder_path: str,
        title: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
        remove_attributes: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Update folder."""
        data = {}
        if title:
            data["title"] = title
        if attributes:
            data["attributes"] = attributes
        if remove_attributes:
            data["remove_attributes"] = remove_attributes

        endpoint = f"objects/folder_config/{quote(folder_path)}"
        return await self._request("PUT", endpoint, data=data)

    async def delete_folder(self, folder_path: str, delete_mode: str = "recursive") -> None:
        """Delete folder."""
        params = {"delete_mode": delete_mode}
        endpoint = f"objects/folder_config/{quote(folder_path)}"
        await self._request("DELETE", endpoint, params=params)

    async def move_folder(self, folder_path: str, destination: str) -> Dict[str, Any]:
        """Move folder."""
        data = {"destination": destination}
        endpoint = f"objects/folder_config/{quote(folder_path)}/actions/move"
        return await self._request("POST", endpoint, data=data)

    async def bulk_update_folders(self, folders: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Update multiple folders."""
        data = {"entries": folders}
        return await self._request("PUT", "domain-types/folder_config/actions/bulk-update", data=data)

    async def get_hosts_in_folder(
        self,
        folder_path: str,
        effective_attributes: bool = False,
    ) -> Dict[str, Any]:
        """Get hosts in folder."""
        params = {"folder": folder_path}
        if effective_attributes:
            params["effective_attributes"] = "true"

        return await self._request("GET", "objects/host_config", params=params)

    # Host Groups

    async def get_host_groups(self) -> Dict[str, Any]:
        """Get all host groups."""
        return await self._request("GET", "objects/host_group_config")

    async def get_host_group(self, group_name: str) -> Dict[str, Any]:
        """Get specific host group."""
        endpoint = f"objects/host_group_config/{quote(group_name)}"
        return await self._request("GET", endpoint)

    async def create_host_group(self, name: str, alias: str) -> Dict[str, Any]:
        """Create host group."""
        data = {"name": name, "alias": alias}
        return await self._request("POST", "objects/host_group_config", data=data)

    async def update_host_group(self, name: str, alias: str) -> Dict[str, Any]:
        """Update host group."""
        data = {"alias": alias}
        endpoint = f"objects/host_group_config/{quote(name)}"
        return await self._request("PUT", endpoint, data=data)

    async def delete_host_group(self, name: str) -> None:
        """Delete host group."""
        endpoint = f"objects/host_group_config/{quote(name)}"
        await self._request("DELETE", endpoint)

    async def bulk_update_host_groups(self, groups: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Update multiple host groups."""
        data = {"entries": groups}
        return await self._request("PUT", "domain-types/host_group_config/actions/bulk-update", data=data)

    async def bulk_delete_host_groups(self, group_names: List[str]) -> Dict[str, Any]:
        """Delete multiple host groups."""
        data = {"entries": group_names}
        return await self._request("POST", "domain-types/host_group_config/actions/bulk-delete", data=data)

    # Host Tag Groups

    async def get_all_host_tag_groups(self) -> Dict[str, Any]:
        """Get all host tag groups."""
        return await self._request("GET", "objects/host_tag_group")

    async def get_host_tag_group(self, name: str) -> Dict[str, Any]:
        """Get specific host tag group."""
        endpoint = f"objects/host_tag_group/{quote(name)}"
        return await self._request("GET", endpoint)

    async def create_host_tag_group(
        self,
        id: str,
        title: str,
        tags: List[Dict[str, Any]],
        topic: Optional[str] = None,
        help: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create host tag group."""
        data = {
            "ident": id,
            "title": title,
            "tags": tags,
        }
        if topic:
            data["topic"] = topic
        if help:
            data["help"] = help

        return await self._request("POST", "objects/host_tag_group", data=data)

    async def update_host_tag_group(
        self,
        name: str,
        title: Optional[str] = None,
        tags: Optional[List[Dict[str, Any]]] = None,
        topic: Optional[str] = None,
        help: Optional[str] = None,
        repair: bool = False,
    ) -> Dict[str, Any]:
        """Update host tag group."""
        data = {}
        if title:
            data["title"] = title
        if tags:
            data["tags"] = tags
        if topic:
            data["topic"] = topic
        if help:
            data["help"] = help
        if repair:
            data["repair"] = repair

        endpoint = f"objects/host_tag_group/{quote(name)}"
        return await self._request("PUT", endpoint, data=data)

    async def delete_host_tag_group(
        self,
        name: str,
        repair: bool = False,
        mode: Optional[str] = None,
    ) -> None:
        """Delete host tag group."""
        params = {}
        if repair:
            params["repair"] = "true"
        if mode:
            params["mode"] = mode

        endpoint = f"objects/host_tag_group/{quote(name)}"
        await self._request("DELETE", endpoint, params=params)