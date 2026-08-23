"""Player and world-position models."""

from pydantic import AwareDatetime, Field

from sevendtd.models.common import ProtocolModel


class WorldPosition(ProtocolModel):
    x: float
    y: float
    z: float


class WorldHorizontalPosition(ProtocolModel):
    x: float
    z: float


class PlatformIdentity(ProtocolModel):
    combined_string: str = Field(alias="combinedString")
    platform_id: str = Field(alias="platformId")
    user_id: str = Field(alias="userId")


class KillCounts(ProtocolModel):
    zombies: int
    players: int


class BanInformation(ProtocolModel):
    ban_active: bool = Field(alias="banActive")
    reason: str | None
    until: AwareDatetime | None


class Player(ProtocolModel):
    entity_id: int = Field(alias="entityId")
    name: str
    platform_id: PlatformIdentity = Field(alias="platformId")
    crossplatform_id: PlatformIdentity = Field(alias="crossplatformId")
    total_play_time_seconds: int | None = Field(alias="totalPlayTimeSeconds")
    last_online: AwareDatetime | None = Field(alias="lastOnline")
    online: bool
    ip: str
    ping: int
    position: WorldPosition
    level: int
    health: int
    stamina: int
    score: int
    deaths: int
    kills: KillCounts
    banned: BanInformation


class PlayersData(ProtocolModel):
    players: tuple[Player, ...]


class OnlinePlayers(PlayersData):
    observed_at: AwareDatetime
