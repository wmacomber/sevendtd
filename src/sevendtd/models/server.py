"""Server information and statistics models."""

from typing import Any

from pydantic import AwareDatetime, Field, PrivateAttr, model_validator

from sevendtd.exceptions import SevenDTDInvalidResponseError
from sevendtd.models.common import JsonValue, ProtocolModel


class ServerProperty(ProtocolModel):
    name: str
    type_name: str = Field(alias="type")
    value: JsonValue

    @model_validator(mode="after")
    def _validate_known_type(self) -> "ServerProperty":
        valid = {
            "string": isinstance(self.value, str),
            "int": isinstance(self.value, int) and not isinstance(self.value, bool),
            "bool": isinstance(self.value, bool),
        }
        if self.type_name in valid and not valid[self.type_name]:
            raise ValueError(f"property {self.name!r} does not match type {self.type_name!r}")
        return self


class ServerInfo(ProtocolModel):
    properties: tuple[ServerProperty, ...]
    observed_at: AwareDatetime
    _index: dict[str, tuple[ServerProperty, ...]] = PrivateAttr(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        index: dict[str, list[ServerProperty]] = {}
        for item in self.properties:
            index.setdefault(item.name, []).append(item)
        self._index = {name: tuple(items) for name, items in index.items()}

    def get(self, name: str, default: JsonValue = None) -> JsonValue:
        matches = self._index.get(name)
        return matches[-1].value if matches else default

    def get_all(self, name: str) -> tuple[ServerProperty, ...]:
        return self._index.get(name, ())

    def _typed(self, name: str, expected: type[Any]) -> Any | None:
        matches = self._index.get(name)
        if not matches:
            return None
        value = matches[-1].value
        if expected is int:
            valid = isinstance(value, int) and not isinstance(value, bool)
        else:
            valid = isinstance(value, expected)
        if not valid:
            raise SevenDTDInvalidResponseError(
                f"server property {name!r} has unexpected runtime type"
            )
        return value

    @property
    def game_name(self) -> str | None:
        return self._typed("GameName", str)

    @property
    def server_version(self) -> str | None:
        return self._typed("ServerVersion", str)

    @property
    def max_players(self) -> int | None:
        return self._typed("MaxPlayers", int)

    @property
    def current_players(self) -> int | None:
        return self._typed("CurrentPlayers", int)

    @property
    def world_size(self) -> int | None:
        return self._typed("WorldSize", int)


class GameTime(ProtocolModel):
    days: int
    hours: int
    minutes: int


class ServerStatsData(ProtocolModel):
    game_time: GameTime = Field(alias="gameTime")
    players: int
    hostiles: int
    animals: int


class ServerStats(ServerStatsData):
    observed_at: AwareDatetime
