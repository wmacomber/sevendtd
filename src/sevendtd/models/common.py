"""Shared inbound protocol models."""

from typing import TypeVar

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

type JsonValue = bool | int | float | str | list[JsonValue] | dict[str, JsonValue] | None


class ProtocolModel(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class ResponseMeta(ProtocolModel):
    server_time: AwareDatetime = Field(alias="serverTime")


T = TypeVar("T")


class ResponseEnvelope(ProtocolModel):
    data: object
    meta: ResponseMeta
