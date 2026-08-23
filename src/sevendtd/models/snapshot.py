"""Concurrent current-state snapshot models."""

from pydantic import AwareDatetime

from sevendtd.models.common import ProtocolModel
from sevendtd.models.entities import AnimalCollection, HostileCollection
from sevendtd.models.map import MapConfig
from sevendtd.models.players import OnlinePlayers
from sevendtd.models.server import ServerInfo, ServerStats


class SnapshotFailure(ProtocolModel):
    component: str
    error_type: str
    message: str


class ServerSnapshot(ProtocolModel):
    server_info: ServerInfo | None = None
    server_stats: ServerStats | None = None
    online_players: OnlinePlayers | None = None
    hostiles: HostileCollection | None = None
    animals: AnimalCollection | None = None
    map_config: MapConfig | None = None
    capture_started_at: AwareDatetime
    capture_finished_at: AwareDatetime
    failures: tuple[SnapshotFailure, ...] = ()

    @property
    def complete(self) -> bool:
        return not self.failures
