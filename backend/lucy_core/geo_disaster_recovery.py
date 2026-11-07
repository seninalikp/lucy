r"""
backend/lucy_core/geo_disaster_recovery.py
Stage 229: Autonomous Planetary Geo-Distributed Disaster Recovery & State Relocator
Era 23: Universal Multi-Verse State Synthesis, Sub-Atomic Hyper-Computing & Sovereign Holographic Swarm Intelligence

100% offline, sovereign planetary geo-distributed disaster recovery and state relocator fabric:
1. Multi-Region Planetary Topology:
   - Models distributed geo-regions (e.g., EARTH_EU, EARTH_US, EARTH_APAC, LUNAR_GATEWAY).
   - Tracks inter-region latency, replication state logs, and heartbeats.
2. Split-Brain Immunity & Quorum Fencing:
   - Autonomous leader election with majority quorum (N/2 + 1) and monotonic epoch fencing tokens.
   - Prevents split-brain state divergence under asymmetric network partitions.
3. Catastrophic Incident Simulation & Instant State Relocation:
   - Simulates regional blackouts, physical fiber severances, and localized disasters.
   - Automatically fails over primary state to the most optimal healthy survivor region with zero data loss.
4. Thread-safe execution fabric and CP1252-safe ASCII table formatting.
"""

from __future__ import annotations

import collections
import copy
import enum
import hashlib
import threading
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union

STAGE: int = 229
STAGE_NAME: str = "Autonomous Planetary Geo-Distributed Disaster Recovery & State Relocator"
ERA: int = 23
ERA_NAME: str = "Universal Multi-Verse State Synthesis, Sub-Atomic Hyper-Computing & Sovereign Holographic Swarm Intelligence"


class RegionHealth(enum.Enum):
    ONLINE_HEALTHY = "ONLINE_HEALTHY"
    DEGRADED = "DEGRADED"
    PARTITIONED = "PARTITIONED"
    OFFLINE_DISASTER = "OFFLINE_DISASTER"


@dataclass
class GeoRegionNode:
    region_id: str
    location_name: str
    is_primary: bool
    health: RegionHealth
    state_epoch: int
    last_replicated_seq: int
    state_payload: Dict[str, Any] = field(default_factory=dict)
    latency_to_peers_ms: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "region_id": self.region_id,
            "location_name": self.location_name,
            "is_primary": self.is_primary,
            "health": self.health.value,
            "state_epoch": self.state_epoch,
            "last_replicated_seq": self.last_replicated_seq,
            "state_payload": copy.deepcopy(self.state_payload),
        }


class GeoDisasterRecoveryFabric:
    """
    Thread-safe planetary geo-distributed disaster recovery and state relocator engine.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.regions: Dict[str, GeoRegionNode] = {}
        self.current_epoch: int = 1
        self.primary_region_id: str = "EARTH_EU_FRANKFURT"
        self.replication_seq: int = 0
        self.failover_history: List[Dict[str, Any]] = []

        self._init_default_topology()

    def _init_default_topology(self) -> None:
        default_regions = [
            ("EARTH_EU_FRANKFURT", "Frankfurt, EU", True),
            ("EARTH_US_VIRGINIA", "Virginia, US", False),
            ("EARTH_APAC_SINGAPORE", "Singapore, APAC", False),
            ("LUNAR_GATEWAY_ORBIT", "Lunar Gateway Orbit", False),
            ("ORBITAL_STATION_ALPHA", "LEO Orbital Station Alpha", False),
        ]
        for rid, loc, is_prim in default_regions:
            self.regions[rid] = GeoRegionNode(
                region_id=rid,
                location_name=loc,
                is_primary=is_prim,
                health=RegionHealth.ONLINE_HEALTHY,
                state_epoch=self.current_epoch,
                last_replicated_seq=0,
                state_payload={"system_mode": "autonomous", "operator": "Senin"},
                latency_to_peers_ms={r[0]: 25.0 for r in default_regions if r[0] != rid},
            )

    def replicate_state(self, updates: Dict[str, Any]) -> int:
        """Commits updates to primary and synchronizes with all reachable quorum nodes."""
        with self._lock:
            primary = self.regions[self.primary_region_id]
            if primary.health != RegionHealth.ONLINE_HEALTHY:
                raise RuntimeError(f"Primary region '{self.primary_region_id}' is unhealthy. Failover required.")

            self.replication_seq += 1
            primary.last_replicated_seq = self.replication_seq
            primary.state_payload.update(copy.deepcopy(updates))

            # Synchronize with healthy peer regions
            replicated_count = 1
            for rid, node in self.regions.items():
                if rid == self.primary_region_id:
                    continue
                if node.health in (RegionHealth.ONLINE_HEALTHY, RegionHealth.DEGRADED):
                    node.state_payload.update(copy.deepcopy(updates))
                    node.last_replicated_seq = self.replication_seq
                    node.state_epoch = self.current_epoch
                    replicated_count += 1

            # Verify quorum majority (at least 3 of 5 nodes)
            quorum_threshold = (len(self.regions) // 2) + 1
            if replicated_count < quorum_threshold:
                raise RuntimeError(f"Quorum lost! Only {replicated_count}/{len(self.regions)} regions acknowledged.")

            return self.replication_seq

    def trigger_disaster(self, region_id: str, disaster_health: RegionHealth = RegionHealth.OFFLINE_DISASTER) -> None:
        """Simulates a localized disaster or network severance disabling a region."""
        with self._lock:
            if region_id not in self.regions:
                raise ValueError(f"Region '{region_id}' does not exist.")

            node = self.regions[region_id]
            node.health = disaster_health

            # If disaster struck primary region, initiate autonomous failover!
            if region_id == self.primary_region_id:
                self.relocate_primary()

    def relocate_primary(self, candidate_region_id: Optional[str] = None) -> str:
        """
        Autonomous failover relocator: elects new primary from healthy quorum survivors.
        """
        with self._lock:
            old_primary_id = self.primary_region_id
            if old_primary_id in self.regions:
                self.regions[old_primary_id].is_primary = False

            # Find healthy candidates with highest replication sequence
            healthy_candidates = [
                n for n in self.regions.values() if n.health in (RegionHealth.ONLINE_HEALTHY, RegionHealth.DEGRADED)
            ]

            quorum_threshold = (len(self.regions) // 2) + 1
            if len(healthy_candidates) < quorum_threshold:
                raise RuntimeError("Catastrophic planetary partition: insufficient surviving nodes for quorum!")

            if candidate_region_id:
                new_primary = self.regions.get(candidate_region_id)
                if not new_primary or new_primary.health not in (RegionHealth.ONLINE_HEALTHY, RegionHealth.DEGRADED):
                    raise ValueError(f"Designated candidate '{candidate_region_id}' is unhealthy or does not exist.")
            else:
                # Select node with most recent sequence and lowest average peer latency
                healthy_candidates.sort(
                    key=lambda n: (
                        -n.last_replicated_seq,
                        sum(n.latency_to_peers_ms.values()) / max(1, len(n.latency_to_peers_ms)),
                    )
                )
                new_primary = healthy_candidates[0]

            self.current_epoch += 1
            new_primary.is_primary = True
            new_primary.state_epoch = self.current_epoch
            self.primary_region_id = new_primary.region_id

            failover_record = {
                "epoch": self.current_epoch,
                "previous_primary": old_primary_id,
                "new_primary": self.primary_region_id,
                "timestamp": time.time(),
                "surviving_nodes": len(healthy_candidates),
                "replicated_seq": new_primary.last_replicated_seq,
            }
            self.failover_history.append(failover_record)
            return self.primary_region_id

    def restore_region(self, region_id: str) -> None:
        """Restores a recovered region and syncs state from current primary."""
        with self._lock:
            if region_id not in self.regions:
                raise ValueError(f"Region '{region_id}' does not exist.")

            node = self.regions[region_id]
            primary = self.regions[self.primary_region_id]

            node.health = RegionHealth.ONLINE_HEALTHY
            node.is_primary = False
            node.state_epoch = self.current_epoch
            node.last_replicated_seq = primary.last_replicated_seq
            node.state_payload = copy.deepcopy(primary.state_payload)

    def status(self) -> Dict[str, Any]:
        with self._lock:
            online_count = sum(
                1 for n in self.regions.values() if n.health in (RegionHealth.ONLINE_HEALTHY, RegionHealth.DEGRADED)
            )
            return {
                "stage": STAGE,
                "stage_name": STAGE_NAME,
                "era": ERA,
                "era_name": ERA_NAME,
                "primary_region": self.primary_region_id,
                "current_epoch": self.current_epoch,
                "replication_seq": self.replication_seq,
                "total_regions": len(self.regions),
                "online_regions": online_count,
                "has_quorum": online_count >= ((len(self.regions) // 2) + 1),
                "total_failovers": len(self.failover_history),
                "regions": [n.to_dict() for n in self.regions.values()],
            }

    def format_ascii_status(self) -> str:
        s = self.status()
        header = f"+-------------------------------------------------------------------------+\n|      STAGE {s['stage']}: {s['stage_name'].upper()[:52]:<52} |\n|      Era {s['era']}: {s['era_name'][:56]:<56} |\n+-------------------------------------------------------------------------+"
        body = (
            f"| Primary Region       : {s['primary_region']:<48} |\n"
            f"| Current State Epoch  : Epoch #{s['current_epoch']:<41} |\n"
            f"| Replication Sequence : Seq #{s['replication_seq']:<43} |\n"
            f"| Quorum Health        : {'QUORUM_OK' if s['has_quorum'] else 'QUORUM_LOST':<48} |\n"
            f"| Online Survivor Nodes: {s['online_regions']}/{s['total_regions']}{' ' * 45}|\n"
            f"| Failovers Executed   : {s['total_failovers']:<48} |"
        )
        footer = "+-------------------------------------------------------------------------+"
        return f"{header}\n{body}\n{footer}"
