"""Raw command response model."""

from pydantic import AwareDatetime

from sevendtd.models.common import ProtocolModel


class CommandData(ProtocolModel):
    command: str
    parameters: str
    result: str


class CommandResult(CommandData):
    observed_at: AwareDatetime
