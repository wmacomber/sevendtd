"""Semantic administrative command namespace."""

from collections.abc import Mapping

from sevendtd.admin.builders import (
    prepare_ban,
    prepare_ban_list,
    prepare_get_time,
    prepare_give,
    prepare_kick,
    prepare_message,
    prepare_save_world,
    prepare_say,
    prepare_shutdown,
    prepare_unban,
)
from sevendtd.admin.metadata import (
    ADMIN_OPERATIONS,
    AdminOperationMetadata,
    BanDurationUnit,
    PreparedCommand,
)
from sevendtd.models.commands import CommandResult
from sevendtd.resources.commands import CommandsNamespace


class AdminNamespace:
    def __init__(self, commands: CommandsNamespace) -> None:
        self._commands = commands

    @property
    def operations(self) -> Mapping[str, AdminOperationMetadata]:
        return ADMIN_OPERATIONS

    def prepare_get_time(self) -> PreparedCommand:
        return prepare_get_time()

    def prepare_save_world(self) -> PreparedCommand:
        return prepare_save_world()

    def prepare_shutdown(self) -> PreparedCommand:
        return prepare_shutdown()

    def prepare_give(
        self,
        entity_id: int,
        item_name: str,
        amount: int,
        quality: int | None = None,
    ) -> PreparedCommand:
        return prepare_give(entity_id, item_name, amount, quality)

    def prepare_say(self, message: str) -> PreparedCommand:
        return prepare_say(message)

    def prepare_message(self, entity_id: int, message: str) -> PreparedCommand:
        return prepare_message(entity_id, message)

    def prepare_kick(self, entity_id: int, reason: str | None = None) -> PreparedCommand:
        return prepare_kick(entity_id, reason)

    def prepare_ban(
        self,
        entity_id: int,
        duration: int,
        unit: BanDurationUnit,
        reason: str | None = None,
    ) -> PreparedCommand:
        return prepare_ban(entity_id, duration, unit, reason)

    def prepare_ban_list(self) -> PreparedCommand:
        return prepare_ban_list()

    def prepare_unban(self, combined_identity: str) -> PreparedCommand:
        return prepare_unban(combined_identity)

    async def execute(self, prepared: PreparedCommand) -> CommandResult:
        return await self._commands.execute(
            prepared.text,
            operation=prepared.metadata.name,
            risk=prepared.metadata.risk.value,
        )

    async def get_time(self) -> CommandResult:
        return await self.execute(self.prepare_get_time())

    async def save_world(self) -> CommandResult:
        return await self.execute(self.prepare_save_world())

    async def shutdown(self) -> CommandResult:
        return await self.execute(self.prepare_shutdown())

    async def give(
        self,
        entity_id: int,
        item_name: str,
        amount: int,
        quality: int | None = None,
    ) -> CommandResult:
        return await self.execute(self.prepare_give(entity_id, item_name, amount, quality))

    async def say(self, message: str) -> CommandResult:
        return await self.execute(self.prepare_say(message))

    async def message(self, entity_id: int, message: str) -> CommandResult:
        return await self.execute(self.prepare_message(entity_id, message))

    async def kick(self, entity_id: int, reason: str | None = None) -> CommandResult:
        return await self.execute(self.prepare_kick(entity_id, reason))

    async def ban(
        self,
        entity_id: int,
        duration: int,
        unit: BanDurationUnit,
        reason: str | None = None,
    ) -> CommandResult:
        return await self.execute(self.prepare_ban(entity_id, duration, unit, reason))

    async def ban_list(self) -> CommandResult:
        return await self.execute(self.prepare_ban_list())

    async def unban(self, combined_identity: str) -> CommandResult:
        return await self.execute(self.prepare_unban(combined_identity))
