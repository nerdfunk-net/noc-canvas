"""
Topology builder service for constructing network topology from cached data.
Builds topology graphs from CDP neighbors, routing tables, and Layer 2 data.
"""

import logging
import math
from typing import List, Optional, Dict, Tuple, Set
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..models.device_cache import (
    DeviceCache, CDPNeighborCache, StaticRouteCache,
    OSPFRouteCache, BGPRouteCache, ARPCache, MACAddressTableCache,
    IPAddressCache
)
from ..schemas.topology import (
    TopologyNode, TopologyLink, TopologyGraph, LinkType,
    TopologyStatistics, NeighborResolution
)

logger = logging.getLogger(__name__)


class TopologyBuilderService:
    """Service for building network topology from cached data."""

    @staticmethod
    def build_topology_from_cache(
        db: Session,
        device_ids: Optional[List[str]] = None,
        include_cdp: bool = True,
        include_routing: bool = False,
        route_types: List[str] = ["static", "ospf", "bgp"],
        include_layer2: bool = False,
        auto_layout: bool = True,
        layout_algorithm: str = "force_directed"
    ) -> TopologyGraph:
        """
        Build complete topology from cache data.

        Args:
            db: Database session
            device_ids: List of device IDs to include (None = all cached devices)
            include_cdp: Include CDP/LLDP neighbor links
            include_routing: Include routing table links
            route_types: Types of routes to include (static, ospf, bgp)
            include_layer2: Include Layer 2 MAC/ARP links
            auto_layout: Calculate node positions automatically
            layout_algorithm: Layout algorithm to use (force_directed, hierarchical, circular)

        Returns:
            TopologyGraph with nodes and links
        """
        logger.info(f"Building topology from cache. Devices: {device_ids or 'all'}")

        # Get devices
        query = db.query(DeviceCache)
        if device_ids:
            query = query.filter(DeviceCache.device_id.in_(device_ids))
        devices = query.all()

        if not devices:
            logger.warning("No devices found for topology building")
            return TopologyGraph(nodes=[], links=[], metadata={"device_count": 0, "link_count": 0})

        # Build nodes
        nodes = TopologyBuilderService._build_nodes(devices)

        # Collect all links
        all_links = []

        if include_cdp:
            cdp_links = TopologyBuilderService._extract_cdp_links(db, devices)
            all_links.extend(cdp_links)
            logger.info(f"Extracted {len(cdp_links)} CDP links")

        if include_routing:
            routing_links = TopologyBuilderService._extract_routing_links(db, devices, route_types)
            all_links.extend(routing_links)
            logger.info(f"Extracted {len(routing_links)} routing links")

        if include_layer2:
            layer2_links = TopologyBuilderService._extract_layer2_links(db, devices)
            all_links.extend(layer2_links)
            logger.info(f"Extracted {len(layer2_links)} Layer 2 links")

        # Deduplicate links
        links = TopologyBuilderService._deduplicate_links(all_links)
        logger.info(f"Deduplicated to {len(links)} unique links")

        # Calculate positions if requested
        if auto_layout and nodes:
            positions = TopologyBuilderService._calculate_layout_positions(
                nodes, links, algorithm=layout_algorithm
            )
            for node in nodes:
                if node.device_id in positions:
                    node.position_x, node.position_y = positions[node.device_id]

        metadata = {
            "device_count": len(nodes),
            "link_count": len(links),
            "include_cdp": include_cdp,
            "include_routing": include_routing,
            "include_layer2": include_layer2,
            "layout_algorithm": layout_algorithm if auto_layout else None
        }

        return TopologyGraph(nodes=nodes, links=links, metadata=metadata)

    @staticmethod
    def build_cdp_topology(
        db: Session,
        device_ids: Optional[List[str]] = None,
        auto_layout: bool = True
    ) -> TopologyGraph:
        """Build topology from CDP/LLDP neighbors only."""
        return TopologyBuilderService.build_topology_from_cache(
            db=db,
            device_ids=device_ids,
            include_cdp=True,
            include_routing=False,
            include_layer2=False,
            auto_layout=auto_layout
        )

    @staticmethod
    def build_routing_topology(
        db: Session,
        device_ids: Optional[List[str]] = None,
        route_types: List[str] = ["static", "ospf", "bgp"],
        auto_layout: bool = True
    ) -> TopologyGraph:
        """Build topology from routing tables."""
        return TopologyBuilderService.build_topology_from_cache(
            db=db,
            device_ids=device_ids,
            include_cdp=False,
            include_routing=True,
            route_types=route_types,
            include_layer2=False,
            auto_layout=auto_layout
        )

    @staticmethod
    def build_layer2_topology(
        db: Session,
        device_ids: Optional[List[str]] = None,
        auto_layout: bool = True
    ) -> TopologyGraph:
        """Build topology from MAC/ARP tables."""
        return TopologyBuilderService.build_topology_from_cache(
            db=db,
            device_ids=device_ids,
            include_cdp=False,
            include_routing=False,
            include_layer2=True,
            auto_layout=auto_layout
        )

    @staticmethod
    def _build_nodes(devices: List[DeviceCache]) -> List[TopologyNode]:
        """Convert device cache entries to topology nodes."""
        nodes = []
        for device in devices:
            node = TopologyNode(
                device_id=device.device_id,
                device_name=device.device_name,
                primary_ip=device.primary_ip,
                platform=device.platform,
                metadata={
                    "polling_enabled": device.polling_enabled,
                    "last_updated": device.last_updated.isoformat() if device.last_updated else None,
                    "cache_valid_until": device.cache_valid_until.isoformat() if device.cache_valid_until else None
                }
            )
            nodes.append(node)
        return nodes

    @staticmethod
    def _extract_cdp_links(db: Session, devices: List[DeviceCache]) -> List[TopologyLink]:
        """Extract links from CDP neighbor cache."""
        links = []
        device_ids = [d.device_id for d in devices]

        # Query all CDP neighbors for these devices
        cdp_neighbors = db.query(CDPNeighborCache).filter(
            CDPNeighborCache.device_id.in_(device_ids)
        ).all()

        logger.info(f"Processing {len(cdp_neighbors)} CDP neighbor entries")

        for cdp in cdp_neighbors:
            # Resolve neighbor to device_id
            neighbor_device_id = TopologyBuilderService._resolve_neighbor_device_id(
                db, cdp.neighbor_name, cdp.neighbor_ip
            )

            if not neighbor_device_id:
                logger.debug(f"Could not resolve CDP neighbor: {cdp.neighbor_name} ({cdp.neighbor_ip})")
                continue

            # Get device names
            source_device = next((d for d in devices if d.device_id == cdp.device_id), None)
            target_device = db.query(DeviceCache).filter(
                DeviceCache.device_id == neighbor_device_id
            ).first()

            if not source_device or not target_device:
                continue

            link = TopologyLink(
                source_device_id=cdp.device_id,
                target_device_id=neighbor_device_id,
                source_device_name=source_device.device_name,
                target_device_name=target_device.device_name,
                source_interface=cdp.local_interface,
                target_interface=cdp.neighbor_interface,
                link_type=LinkType.CDP_NEIGHBOR,
                bidirectional=True,
                link_metadata={
                    "neighbor_platform": cdp.platform,
                    "neighbor_capabilities": cdp.capabilities
                }
            )
            links.append(link)

        return links

    @staticmethod
    def _extract_routing_links(
        db: Session,
        devices: List[DeviceCache],
        route_types: List[str]
    ) -> List[TopologyLink]:
        """Extract links from routing tables."""
        links = []
        device_ids = [d.device_id for d in devices]

        # Extract static route links
        if "static" in route_types:
            static_routes = db.query(StaticRouteCache).filter(
                StaticRouteCache.device_id.in_(device_ids)
            ).all()

            for route in static_routes:
                if not route.nexthop_ip:
                    continue

                # Find which device owns the nexthop IP
                nexthop_device = TopologyBuilderService._find_device_by_ip(db, route.nexthop_ip)
                if not nexthop_device:
                    continue

                source_device = next((d for d in devices if d.device_id == route.device_id), None)
                if not source_device:
                    continue

                link = TopologyLink(
                    source_device_id=route.device_id,
                    target_device_id=nexthop_device.device_id,
                    source_device_name=source_device.device_name,
                    target_device_name=nexthop_device.device_name,
                    source_interface=route.interface_name,
                    target_interface=None,
                    link_type=LinkType.STATIC_ROUTE,
                    bidirectional=False,
                    link_metadata={
                        "network": route.network,
                        "nexthop_ip": route.nexthop_ip,
                        "metric": route.metric,
                        "distance": route.distance
                    }
                )
                links.append(link)

        # Extract OSPF route links
        if "ospf" in route_types:
            ospf_routes = db.query(OSPFRouteCache).filter(
                OSPFRouteCache.device_id.in_(device_ids)
            ).all()

            for route in ospf_routes:
                if not route.nexthop_ip:
                    continue

                nexthop_device = TopologyBuilderService._find_device_by_ip(db, route.nexthop_ip)
                if not nexthop_device:
                    continue

                source_device = next((d for d in devices if d.device_id == route.device_id), None)
                if not source_device:
                    continue

                link = TopologyLink(
                    source_device_id=route.device_id,
                    target_device_id=nexthop_device.device_id,
                    source_device_name=source_device.device_name,
                    target_device_name=nexthop_device.device_name,
                    source_interface=route.interface_name,
                    target_interface=None,
                    link_type=LinkType.OSPF_ROUTE,
                    bidirectional=False,
                    link_metadata={
                        "network": route.network,
                        "nexthop_ip": route.nexthop_ip,
                        "metric": route.metric,
                        "area": route.area,
                        "route_type": route.route_type
                    }
                )
                links.append(link)

        # Extract BGP route links
        if "bgp" in route_types:
            bgp_routes = db.query(BGPRouteCache).filter(
                BGPRouteCache.device_id.in_(device_ids)
            ).all()

            for route in bgp_routes:
                if not route.nexthop_ip:
                    continue

                nexthop_device = TopologyBuilderService._find_device_by_ip(db, route.nexthop_ip)
                if not nexthop_device:
                    continue

                source_device = next((d for d in devices if d.device_id == route.device_id), None)
                if not source_device:
                    continue

                link = TopologyLink(
                    source_device_id=route.device_id,
                    target_device_id=nexthop_device.device_id,
                    source_device_name=source_device.device_name,
                    target_device_name=nexthop_device.device_name,
                    source_interface=None,
                    target_interface=None,
                    link_type=LinkType.BGP_ROUTE,
                    bidirectional=False,
                    link_metadata={
                        "network": route.network,
                        "nexthop_ip": route.nexthop_ip,
                        "as_path": route.as_path,
                        "local_pref": route.local_pref,
                        "metric": route.metric
                    }
                )
                links.append(link)

        return links

    @staticmethod
    def _extract_layer2_links(db: Session, devices: List[DeviceCache]) -> List[TopologyLink]:
        """Extract links from MAC/ARP tables."""
        links = []
        device_ids = [d.device_id for d in devices]

        # Get ARP entries for these devices
        arp_entries = db.query(ARPCache).filter(
            ARPCache.device_id.in_(device_ids)
        ).all()

        for arp in arp_entries:
            # Find which device has this IP
            target_device = TopologyBuilderService._find_device_by_ip(db, arp.ip_address)
            if not target_device or target_device.device_id == arp.device_id:
                continue

            source_device = next((d for d in devices if d.device_id == arp.device_id), None)
            if not source_device:
                continue

            link = TopologyLink(
                source_device_id=arp.device_id,
                target_device_id=target_device.device_id,
                source_device_name=source_device.device_name,
                target_device_name=target_device.device_name,
                source_interface=arp.interface_name,
                target_interface=None,
                link_type=LinkType.ARP_DISCOVERED,
                bidirectional=False,
                link_metadata={
                    "ip_address": arp.ip_address,
                    "mac_address": arp.mac_address,
                    "age": arp.age
                }
            )
            links.append(link)

        return links

    @staticmethod
    def _resolve_neighbor_device_id(
        db: Session,
        neighbor_name: str,
        neighbor_ip: Optional[str]
    ) -> Optional[str]:
        """
        Resolve neighbor name/IP to device_id in cache.

        Returns:
            device_id if found, None otherwise
        """
        # Try exact name match first
        if neighbor_name:
            # Clean up neighbor name (remove domain suffix if present)
            clean_name = neighbor_name.split('.')[0] if '.' in neighbor_name else neighbor_name

            device = db.query(DeviceCache).filter(
                or_(
                    DeviceCache.device_name == neighbor_name,
                    DeviceCache.device_name == clean_name,
                    DeviceCache.device_name.like(f"{clean_name}%")
                )
            ).first()

            if device:
                return device.device_id

        # Try IP match
        if neighbor_ip:
            device = db.query(DeviceCache).filter(
                DeviceCache.primary_ip == neighbor_ip
            ).first()

            if device:
                return device.device_id

            # Also check if IP is assigned to any device interface
            ip_entry = db.query(IPAddressCache).filter(
                IPAddressCache.ip_address == neighbor_ip
            ).first()

            if ip_entry:
                return ip_entry.device_id

        return None

    @staticmethod
    def _find_device_by_ip(db: Session, ip_address: str) -> Optional[DeviceCache]:
        """Find device that owns a specific IP address."""
        # Check primary IP
        device = db.query(DeviceCache).filter(
            DeviceCache.primary_ip == ip_address
        ).first()

        if device:
            return device

        # Check interface IPs
        ip_entry = db.query(IPAddressCache).filter(
            IPAddressCache.ip_address == ip_address
        ).first()

        if ip_entry:
            return db.query(DeviceCache).filter(
                DeviceCache.device_id == ip_entry.device_id
            ).first()

        return None

    @staticmethod
    def _deduplicate_links(links: List[TopologyLink]) -> List[TopologyLink]:
        """
        Remove duplicate bidirectional links.
        Keep only one link for each bidirectional pair.
        """
        unique_links = []
        seen_pairs: Set[Tuple[str, str]] = set()

        for link in links:
            # For bidirectional links, create normalized pair
            if link.bidirectional:
                pair = tuple(sorted([link.source_device_id, link.target_device_id]))
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)

            unique_links.append(link)

        return unique_links

    @staticmethod
    def _calculate_layout_positions(
        nodes: List[TopologyNode],
        links: List[TopologyLink],
        algorithm: str = "force_directed"
    ) -> Dict[str, Tuple[float, float]]:
        """
        Calculate x/y positions for nodes using graph layout algorithm.

        Args:
            nodes: List of topology nodes
            links: List of topology links
            algorithm: Layout algorithm (force_directed, hierarchical, circular)

        Returns:
            Dictionary mapping device_id to (x, y) position
        """
        if not nodes:
            return {}

        if algorithm == "circular":
            return TopologyBuilderService._circular_layout(nodes)
        elif algorithm == "hierarchical":
            return TopologyBuilderService._hierarchical_layout(nodes, links)
        else:  # force_directed (default)
            return TopologyBuilderService._force_directed_layout(nodes, links)

    @staticmethod
    def _circular_layout(nodes: List[TopologyNode]) -> Dict[str, Tuple[float, float]]:
        """Arrange nodes in a circle."""
        positions = {}
        n = len(nodes)
        radius = 300
        center_x, center_y = 400, 300

        for i, node in enumerate(nodes):
            angle = 2 * math.pi * i / n
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            positions[node.device_id] = (x, y)

        return positions

    @staticmethod
    def _hierarchical_layout(
        nodes: List[TopologyNode],
        links: List[TopologyLink]
    ) -> Dict[str, Tuple[float, float]]:
        """Arrange nodes in hierarchical layers."""
        # Simple hierarchical layout based on connection count
        positions = {}

        # Count connections per node
        connection_counts = {}
        for node in nodes:
            count = sum(1 for link in links if link.source_device_id == node.device_id or link.target_device_id == node.device_id)
            connection_counts[node.device_id] = count

        # Sort nodes by connection count (most connected at top)
        sorted_nodes = sorted(nodes, key=lambda n: connection_counts.get(n.device_id, 0), reverse=True)

        # Assign positions in layers
        layer_height = 150
        nodes_per_layer = 5
        x_spacing = 150

        for i, node in enumerate(sorted_nodes):
            layer = i // nodes_per_layer
            position_in_layer = i % nodes_per_layer

            x = 100 + position_in_layer * x_spacing
            y = 100 + layer * layer_height
            positions[node.device_id] = (x, y)

        return positions

    @staticmethod
    def _force_directed_layout(
        nodes: List[TopologyNode],
        links: List[TopologyLink],
        iterations: int = 50
    ) -> Dict[str, Tuple[float, float]]:
        """
        Simple force-directed layout algorithm.
        Simulates springs between connected nodes and repulsion between all nodes.
        """
        # Initialize random positions
        positions = {}
        for i, node in enumerate(nodes):
            positions[node.device_id] = (100 + i * 50, 100 + (i % 5) * 50)

        # Build adjacency for faster lookup
        adjacency = {node.device_id: [] for node in nodes}
        for link in links:
            adjacency[link.source_device_id].append(link.target_device_id)
            if link.bidirectional:
                adjacency[link.target_device_id].append(link.source_device_id)

        # Force-directed algorithm parameters
        spring_length = 150
        spring_strength = 0.1
        repulsion_strength = 10000

        for iteration in range(iterations):
            # Calculate forces
            forces = {node.device_id: [0.0, 0.0] for node in nodes}

            # Spring forces (attraction between connected nodes)
            for link in links:
                src_pos = positions[link.source_device_id]
                tgt_pos = positions[link.target_device_id]

                dx = tgt_pos[0] - src_pos[0]
                dy = tgt_pos[1] - src_pos[1]
                distance = math.sqrt(dx**2 + dy**2) or 1

                force = spring_strength * (distance - spring_length)
                fx = force * dx / distance
                fy = force * dy / distance

                forces[link.source_device_id][0] += fx
                forces[link.source_device_id][1] += fy
                forces[link.target_device_id][0] -= fx
                forces[link.target_device_id][1] -= fy

            # Repulsion forces (repel all nodes from each other)
            for i, node1 in enumerate(nodes):
                for node2 in nodes[i+1:]:
                    pos1 = positions[node1.device_id]
                    pos2 = positions[node2.device_id]

                    dx = pos2[0] - pos1[0]
                    dy = pos2[1] - pos1[1]
                    distance = math.sqrt(dx**2 + dy**2) or 1

                    force = repulsion_strength / (distance**2)
                    fx = force * dx / distance
                    fy = force * dy / distance

                    forces[node1.device_id][0] -= fx
                    forces[node1.device_id][1] -= fy
                    forces[node2.device_id][0] += fx
                    forces[node2.device_id][1] += fy

            # Update positions
            damping = 0.9
            for node in nodes:
                fx, fy = forces[node.device_id]
                x, y = positions[node.device_id]
                positions[node.device_id] = (x + fx * damping, y + fy * damping)

        return positions

    @staticmethod
    def get_topology_statistics(db: Session, topology: TopologyGraph) -> TopologyStatistics:
        """Calculate statistics for a topology graph."""
        # Link types breakdown
        link_types_breakdown = {}
        for link in topology.links:
            link_type = link.link_type.value
            link_types_breakdown[link_type] = link_types_breakdown.get(link_type, 0) + 1

        # Devices by platform
        devices_by_platform = {}
        for node in topology.nodes:
            platform = node.platform or "Unknown"
            devices_by_platform[platform] = devices_by_platform.get(platform, 0) + 1

        # Isolated devices (no links)
        connected_device_ids = set()
        for link in topology.links:
            connected_device_ids.add(link.source_device_id)
            connected_device_ids.add(link.target_device_id)

        isolated_devices = len([n for n in topology.nodes if n.device_id not in connected_device_ids])

        # Average connections per device
        avg_connections = len(topology.links) * 2 / len(topology.nodes) if topology.nodes else 0

        return TopologyStatistics(
            total_devices=len(topology.nodes),
            total_links=len(topology.links),
            link_types_breakdown=link_types_breakdown,
            devices_by_platform=devices_by_platform,
            isolated_devices=isolated_devices,
            average_connections_per_device=round(avg_connections, 2)
        )

    @staticmethod
    def resolve_neighbor(
        db: Session,
        neighbor_name: str,
        neighbor_ip: Optional[str] = None
    ) -> NeighborResolution:
        """Resolve neighbor name/IP to device in cache."""
        device_id = TopologyBuilderService._resolve_neighbor_device_id(db, neighbor_name, neighbor_ip)

        if device_id:
            device = db.query(DeviceCache).filter(DeviceCache.device_id == device_id).first()

            # Determine match confidence
            matched_by = "none"
            confidence = "low"

            if device:
                if device.device_name == neighbor_name and device.primary_ip == neighbor_ip:
                    matched_by = "both"
                    confidence = "high"
                elif device.device_name == neighbor_name:
                    matched_by = "name"
                    confidence = "high"
                elif device.primary_ip == neighbor_ip:
                    matched_by = "ip"
                    confidence = "medium"
                else:
                    matched_by = "partial"
                    confidence = "low"

                return NeighborResolution(
                    neighbor_name=neighbor_name,
                    neighbor_ip=neighbor_ip,
                    device_id=device.device_id,
                    device_name=device.device_name,
                    matched_by=matched_by,
                    confidence=confidence
                )

        return NeighborResolution(
            neighbor_name=neighbor_name,
            neighbor_ip=neighbor_ip,
            device_id=None,
            device_name=None,
            matched_by="none",
            confidence="none"
        )
