"""Raw administrative command resource."""

from sevendtd.exceptions import SevenDTDCommandError, SevenDTDInvalidResponseError
from sevendtd.logging import get_logger, safe_extra
from sevendtd.models.commands import CommandData, CommandResult
from sevendtd.transport.http import HTTPTransport


def validate_command(command: str) -> str:
    if not command or command.isspace():
        raise SevenDTDCommandError("command cannot be empty")
    if any(character in command for character in ("\x00", "\r", "\n")):
        raise SevenDTDCommandError("command cannot contain NUL, CR, or LF")
    return command


class CommandsNamespace:
    def __init__(self, transport: HTTPTransport) -> None:
        self._transport = transport
        self._logger = get_logger()

    async def execute(
        self, command: str, *, operation: str = "raw", risk: str = "UNKNOWN"
    ) -> CommandResult:
        command = validate_command(command)
        try:
            data, meta = await self._transport.request_json(
                "POST",
                "/api/command",
                CommandData,
                resource="commands.execute",
                json={"command": command},
            )
        except SevenDTDInvalidResponseError as exc:
            raise SevenDTDCommandError("invalid command response") from exc
        self._logger.info(
            "command.executed",
            extra=safe_extra({"operation": operation, "risk": risk}),
        )
        return CommandResult(**data.model_dump(), observed_at=meta.server_time)
