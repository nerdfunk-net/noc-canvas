"""
GraphQL queries for Nautobot API interactions.
Centralized location for all Nautobot GraphQL query definitions.
"""

COMPLETE_DEVICE_DATA_QUERY = """
query GetCompleteDeviceData($device_id: ID!) {
  device(id: $device_id) {
    id
    name
    display
    device_type {
      id
      manufacturer {
        name
      }
      model
    }
    role {
      id
      name
    }
    platform {
      id
      name
      network_driver
    }
    location {
      id
      name
      parent {
        name
      }
    }
    status {
      id
      name
    }
    primary_ip4 {
      id
      address
      family
    }
    primary_ip6 {
      id
      address
      family
    }
    serial
    asset_tag
    config_context
    local_config_context_data
    local_config_context_data_owner_content_type {
      model
    }
    local_config_context_data_owner_object_id
    secrets_group {
      id
      name
    }
    tenant {
      id
      name
    }
    cluster {
      id
      name
    }
    virtual_chassis {
      id
      name
    }
    vc_position
    vc_priority
    comments
    last_updated
    created
    custom_fields
    tags {
      id
      name
    }
    cf_last_backup
  }
}
"""

DEVICE_DETAILS_QUERY = """
query DeviceDetails($deviceId: ID!) {
    device(id: $deviceId) {
        id
        name
        hostname: name
        asset_tag
        serial
        position
        face
        config_context
        local_config_context_data
        _custom_field_data
        primary_ip4 {
            id
            address
            description
            ip_version
            host
            mask_length
            dns_name
            status {
                id
                name
            }
            parent {
                id
                prefix
            }
        }
        role {
            id
            name
        }
        device_type {
            id
            model
            manufacturer {
                id
                name
            }
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
        location {
            id
            name
            description
            location_type {
                id
                name
            }
            parent {
                id
                name
                description
                location_type {
                    id
                    name
                }
            }
        }
        status {
            id
            name
        }
        tenant {
            id
            name
            tenant_group {
                name
            }
        }
        rack {
            id
            name
            rack_group {
                id
                name
            }
        }
        tags {
            id
            name
        }
        interfaces {
            id
            name
            description
            enabled
            mac_address
            type
            mode
            mtu
            status {
                id
                name
            }
            ip_addresses {
                address
                status {
                    id
                    name
                }
                role {
                    id
                    name
                }
            }
            tagged_vlans {
                id
                name
                vid
            }
            untagged_vlan {
                id
                name
                vid
            }
        }
        vrfs {
            id
            name
            rd
            description
            namespace {
                id
                name
            }
        }
    }
}
"""

NAMESPACES_QUERY = """
query {
  namespaces {
    id
    name
    description
  }
}
"""

SECRET_GROUPS_QUERY = """
query secrets_groups {
  secrets_groups {
    id
    name
  }
}
"""
