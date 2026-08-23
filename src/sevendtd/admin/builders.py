"""Pure builders. Only command grammar supported by captured evidence is enabled."""

import re

from sevendtd.admin.metadata import (
    BAN,
    BAN_LIST,
    GET_TIME,
    GIVE,
    KICK,
    MESSAGE,
    SAVE_WORLD,
    SAY,
    SEARCH_ITEMS,
    SHUTDOWN,
    UNBAN,
    BanDurationUnit,
    PreparedCommand,
)
from sevendtd.exceptions import SevenDTDCommandError

SAFE_ITEM_NAME = re.compile(r"[A-Za-z0-9_.:-]+", flags=re.ASCII)
UNVERIFIED_TEXT_CHARACTERS = frozenset({'"', "\\", ";", "|", "&"})


def _is_strict_int(value: object) -> bool:
    return type(value) is int


def _is_ban_duration_unit(value: object) -> bool:
    return isinstance(value, BanDurationUnit)


def prepare_get_time() -> PreparedCommand:
    return PreparedCommand("gettime", GET_TIME)


def prepare_save_world() -> PreparedCommand:
    return PreparedCommand("saveworld", SAVE_WORLD)


def prepare_shutdown() -> PreparedCommand:
    return PreparedCommand("shutdown", SHUTDOWN)


def prepare_give(
    entity_id: int,
    item_name: str,
    amount: int,
    quality: int | None = None,
) -> PreparedCommand:
    if not _is_strict_int(entity_id):
        raise SevenDTDCommandError("give entity_id must be an integer")
    if not item_name or SAFE_ITEM_NAME.fullmatch(item_name) is None:
        raise SevenDTDCommandError(
            "give item_name must be one safe token containing only letters, digits, _, ., :, or -"
        )
    if not _is_strict_int(amount) or amount < 1:
        raise SevenDTDCommandError("give amount must be an integer of at least 1")
    if quality is not None and (not _is_strict_int(quality) or not 1 <= quality <= 6):
        raise SevenDTDCommandError("give quality must be an integer from 1 through 6")

    parts = ["give", str(entity_id), item_name, str(amount)]
    if quality is not None:
        parts.append(str(quality))
    return PreparedCommand(" ".join(parts), GIVE)


def prepare_search_items(query: str) -> PreparedCommand:
    if not query or SAFE_ITEM_NAME.fullmatch(query) is None:
        raise SevenDTDCommandError(
            "item search query must be one safe token containing only "
            "letters, digits, _, ., :, or -"
        )
    return PreparedCommand(f"li {query}", SEARCH_ITEMS)


def _quote_console_text(value: str, field: str) -> str:
    if not value or value.isspace():
        raise SevenDTDCommandError(f"{field} cannot be empty")
    if value != value.strip():
        raise SevenDTDCommandError(f"{field} cannot have surrounding whitespace")
    if not value.isprintable():
        raise SevenDTDCommandError(f"{field} cannot contain control characters")
    if any(character in value for character in UNVERIFIED_TEXT_CHARACTERS):
        raise SevenDTDCommandError(
            f"{field} cannot contain double quotes, backslashes, or separators ; | &"
        )
    return f'"{value}"'


def prepare_say(message: str) -> PreparedCommand:
    return PreparedCommand(f"say {_quote_console_text(message, 'say message')}", SAY)


def prepare_message(entity_id: int, message: str) -> PreparedCommand:
    if not _is_strict_int(entity_id):
        raise SevenDTDCommandError("message entity_id must be an integer")
    return PreparedCommand(
        f"pm {entity_id} {_quote_console_text(message, 'private message')}", MESSAGE
    )


def prepare_kick(entity_id: int, reason: str | None = None) -> PreparedCommand:
    if not _is_strict_int(entity_id):
        raise SevenDTDCommandError("kick entity_id must be an integer")
    command = f"kick {entity_id}"
    if reason is not None:
        command = f"{command} {_quote_console_text(reason, 'kick reason')}"
    return PreparedCommand(command, KICK)


def prepare_ban(
    entity_id: int,
    duration: int,
    unit: BanDurationUnit,
    reason: str | None = None,
) -> PreparedCommand:
    if not _is_strict_int(entity_id):
        raise SevenDTDCommandError("ban entity_id must be an integer")
    if not _is_strict_int(duration) or duration < 1:
        raise SevenDTDCommandError("ban duration must be an integer of at least 1")
    if not _is_ban_duration_unit(unit):
        raise SevenDTDCommandError("ban unit must be a BanDurationUnit")
    command = f"ban add {entity_id} {duration} {unit.value}"
    if reason is not None:
        command = f"{command} {_quote_console_text(reason, 'ban reason')}"
    return PreparedCommand(command, BAN)


def prepare_ban_list() -> PreparedCommand:
    return PreparedCommand("ban list", BAN_LIST)


def prepare_unban(combined_identity: str) -> PreparedCommand:
    if not combined_identity or SAFE_ITEM_NAME.fullmatch(combined_identity) is None:
        raise SevenDTDCommandError(
            "unban combined_identity must be one safe cross-platform identity token"
        )
    return PreparedCommand(f"ban remove {combined_identity}", UNBAN)


def unverified_builder(operation: str) -> SevenDTDCommandError:
    return SevenDTDCommandError(
        f"{operation} helper unavailable: live-server argument grammar has not been verified"
    )
