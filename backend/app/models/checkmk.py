"""
CheckMK data models for API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# Base Models


class CheckMKBaseResponse(BaseModel):
    """Base CheckMK response model."""

    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


# Request Models


class CheckMKTestConnectionRequest(BaseModel):
    """CheckMK connection test request."""

    url: str = Field(..., description="CheckMK server URL")
    site: str = Field(..., description="CheckMK site name")
    username: str = Field(..., description="CheckMK username")
    password: str = Field(..., description="CheckMK password")
    verify_ssl: bool = Field(True, description="Verify SSL certificates")


class CheckMKHostCreateRequest(BaseModel):
    """CheckMK host creation request."""

    host_name: str = Field(..., description="Host name")
    folder: str = Field("/", description="Folder path")
    attributes: Dict[str, Any] = Field(
        default_factory=dict, description="Host attributes"
    )
    bake_agent: bool = Field(False, description="Bake agent after creation")


class CheckMKHostUpdateRequest(BaseModel):
    """CheckMK host update request."""

    attributes: Dict[str, Any] = Field(..., description="Host attributes to update")


class CheckMKHostMoveRequest(BaseModel):
    """CheckMK host move request."""

    target_folder: str = Field(..., description="Target folder path")


class CheckMKHostRenameRequest(BaseModel):
    """CheckMK host rename request."""

    new_name: str = Field(..., description="New host name")


class CheckMKBulkHostCreateRequest(BaseModel):
    """CheckMK bulk host creation request."""

    entries: List[CheckMKHostCreateRequest] = Field(
        ..., description="List of hosts to create"
    )


class CheckMKBulkHostUpdateRequest(BaseModel):
    """CheckMK bulk host update request."""

    entries: Dict[str, CheckMKHostUpdateRequest] = Field(
        ..., description="Hosts to update (hostname -> update data)"
    )


class CheckMKBulkHostDeleteRequest(BaseModel):
    """CheckMK bulk host deletion request."""

    entries: List[str] = Field(..., description="List of hostnames to delete")


class CheckMKServiceQueryRequest(BaseModel):
    """CheckMK service query request."""

    columns: Optional[List[str]] = Field(None, description="Columns to retrieve")
    query: Optional[str] = Field(None, description="Query filter")


class CheckMKServiceDiscoveryRequest(BaseModel):
    """CheckMK service discovery request."""

    mode: str = Field("new", description="Discovery mode")


class CheckMKDiscoveryPhaseUpdateRequest(BaseModel):
    """CheckMK discovery phase update request."""

    phase: str = Field(..., description="Discovery phase")
    services: Optional[List[str]] = Field(None, description="Service list")


class CheckMKAcknowledgeHostRequest(BaseModel):
    """CheckMK host problem acknowledgment request."""

    host_name: str = Field(..., description="Host name")
    comment: str = Field(..., description="Acknowledgment comment")
    sticky: bool = Field(True, description="Sticky acknowledgment")
    persistent: bool = Field(False, description="Persistent acknowledgment")
    notify: bool = Field(False, description="Send notifications")


class CheckMKAcknowledgeServiceRequest(BaseModel):
    """CheckMK service problem acknowledgment request."""

    host_name: str = Field(..., description="Host name")
    service_description: str = Field(..., description="Service description")
    comment: str = Field(..., description="Acknowledgment comment")
    sticky: bool = Field(True, description="Sticky acknowledgment")
    persistent: bool = Field(False, description="Persistent acknowledgment")
    notify: bool = Field(False, description="Send notifications")


class CheckMKDowntimeRequest(BaseModel):
    """CheckMK downtime creation request."""

    host_name: str = Field(..., description="Host name")
    start_time: datetime = Field(..., description="Downtime start time")
    end_time: datetime = Field(..., description="Downtime end time")
    comment: str = Field(..., description="Downtime comment")
    downtime_type: str = Field("fixed", description="Downtime type")


class CheckMKCommentRequest(BaseModel):
    """CheckMK comment request."""

    host_name: str = Field(..., description="Host name")
    service_description: Optional[str] = Field(
        None, description="Service description (for service comments)"
    )
    comment: str = Field(..., description="Comment text")
    persistent: bool = Field(False, description="Persistent comment")


class CheckMKActivateChangesRequest(BaseModel):
    """CheckMK configuration activation request."""

    sites: Optional[List[str]] = Field(None, description="Sites to activate")
    force_foreign_changes: bool = Field(False, description="Force foreign changes")
    redirect: bool = Field(False, description="Enable redirect")


class CheckMKHostGroupCreateRequest(BaseModel):
    """CheckMK host group creation request."""

    name: str = Field(..., description="Group name")
    alias: str = Field(..., description="Group alias")


class CheckMKHostGroupUpdateRequest(BaseModel):
    """CheckMK host group update request."""

    alias: str = Field(..., description="Group alias")


class CheckMKHostGroupBulkUpdateRequest(BaseModel):
    """CheckMK bulk host group update request."""

    entries: Dict[str, Dict[str, Any]] = Field(..., description="Groups to update")


class CheckMKHostGroupBulkDeleteRequest(BaseModel):
    """CheckMK bulk host group deletion request."""

    entries: List[str] = Field(..., description="Group names to delete")


class CheckMKFolderCreateRequest(BaseModel):
    """CheckMK folder creation request."""

    name: str = Field(..., description="Folder name")
    title: str = Field(..., description="Folder title")
    parent: str = Field("/", description="Parent folder path")
    attributes: Dict[str, Any] = Field(
        default_factory=dict, description="Folder attributes"
    )


class CheckMKFolderUpdateRequest(BaseModel):
    """CheckMK folder update request."""

    title: Optional[str] = Field(None, description="Folder title")
    attributes: Optional[Dict[str, Any]] = Field(None, description="Folder attributes")
    remove_attributes: Optional[List[str]] = Field(
        None, description="Attributes to remove"
    )


class CheckMKFolderMoveRequest(BaseModel):
    """CheckMK folder move request."""

    destination: str = Field(..., description="Destination folder path")


class CheckMKFolderBulkUpdateRequest(BaseModel):
    """CheckMK bulk folder update request."""

    entries: Dict[str, Dict[str, Any]] = Field(..., description="Folders to update")


class CheckMKHostTagGroupCreateRequest(BaseModel):
    """CheckMK host tag group creation request."""

    id: str = Field(..., description="Tag group ID")
    title: str = Field(..., description="Tag group title")
    tags: List[Dict[str, Any]] = Field(..., description="Tag definitions")
    topic: Optional[str] = Field(None, description="Tag group topic")
    help: Optional[str] = Field(None, description="Tag group help text")


class CheckMKHostTagGroupUpdateRequest(BaseModel):
    """CheckMK host tag group update request."""

    title: Optional[str] = Field(None, description="Tag group title")
    tags: Optional[List[Dict[str, Any]]] = Field(None, description="Tag definitions")
    topic: Optional[str] = Field(None, description="Tag group topic")
    help: Optional[str] = Field(None, description="Tag group help text")
    repair: bool = Field(False, description="Repair conflicts")


# Response Models


class CheckMKTestConnectionResponse(BaseModel):
    """CheckMK connection test response."""

    success: bool
    message: str
    checkmk_url: str
    connection_source: str = "manual_test"


class CheckMKHost(BaseModel):
    """CheckMK host information."""

    host_name: str
    folder: str = "/"
    attributes: Dict[str, Any] = Field(default_factory=dict)
    effective_attributes: Optional[Dict[str, Any]] = None


class CheckMKHostListResponse(BaseModel):
    """CheckMK host list response."""

    hosts: List[CheckMKHost]
    total: int


class CheckMKFolder(BaseModel):
    """CheckMK folder information."""

    name: str
    title: str
    parent: str = "/"
    path: str = "/"
    attributes: Dict[str, Any] = Field(default_factory=dict)
    hosts: Optional[List[str]] = None


class CheckMKFolderListResponse(BaseModel):
    """CheckMK folder list response."""

    folders: List[CheckMKFolder]
    total: int


class CheckMKHostTagGroup(BaseModel):
    """CheckMK host tag group information."""

    id: str
    title: str
    topic: Optional[str] = None
    help: Optional[str] = None
    tags: List[Dict[str, Any]] = Field(default_factory=list)


class CheckMKHostTagGroupListResponse(BaseModel):
    """CheckMK host tag group list response."""

    tag_groups: List[CheckMKHostTagGroup]
    total: int


class CheckMKVersionResponse(BaseModel):
    """CheckMK version information."""

    version: str
    edition: Optional[str] = None
    demo: bool = False


class CheckMKOperationResponse(BaseModel):
    """Generic CheckMK operation response."""

    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class CheckMKStats(BaseModel):
    """CheckMK statistics."""

    total_hosts: int
    timestamp: str


class CheckMKHealthCheck(BaseModel):
    """CheckMK health check response."""

    status: str
    message: str
    total_hosts: Optional[int] = None


# Client-specific models (for CheckMK client integration)


class CheckMKHost(BaseModel):
    """CheckMK host data model."""

    hostname: str
    folder: str = "/"
    attributes: Dict[str, Any] = Field(default_factory=dict)


class CheckMKServiceStatus(BaseModel):
    """CheckMK service status."""

    hostname: str
    service_description: str
    state: int
    plugin_output: str
    last_check: Optional[datetime] = None


class CheckMKHostStatus(BaseModel):
    """CheckMK host status."""

    hostname: str
    state: int
    plugin_output: str
    last_check: Optional[datetime] = None
    services: Optional[List[CheckMKServiceStatus]] = None


# Legacy compatibility models


class CheckMKLegacyResponse(BaseModel):
    """Legacy CheckMK response format."""

    result_code: int = 0
    result: Optional[Dict[str, Any]] = None
    help: Optional[str] = None
