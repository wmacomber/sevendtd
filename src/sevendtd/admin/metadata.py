"""Advisory administrative-operation metadata."""

from dataclasses import dataclass
from enum import StrEnum


class CommandRisk(StrEnum):
    READ_ONLY = "read_only"
    MUTATING = "mutating"
    DESTRUCTIVE = "destructive"
    SERVER_CONTROL = "server_control"
    UNKNOWN = "unknown"


class BanDurationUnit(StrEnum):
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


@dataclass(frozen=True, slots=True)
class AdminOperationMetadata:
    name: str
    console_command: str
    summary: str
    risk: CommandRisk
    syntax_verified: bool = True
    verification_evidence: str | None = None


@dataclass(frozen=True, slots=True)
class PreparedCommand:
    text: str
    metadata: AdminOperationMetadata


GET_TIME = AdminOperationMetadata(
    "get_time",
    "gettime",
    "Read game time",
    CommandRisk.READ_ONLY,
    syntax_verified=False,
    verification_evidence="present in captured generic help; command-specific syntax unavailable",
)
SAVE_WORLD = AdminOperationMetadata(
    "save_world",
    "saveworld",
    "Save world state",
    CommandRisk.MUTATING,
    syntax_verified=False,
    verification_evidence="present in captured generic help; command-specific syntax unavailable",
)
SHUTDOWN = AdminOperationMetadata(
    "shutdown",
    "shutdown",
    "Stop game server",
    CommandRisk.SERVER_CONTROL,
    syntax_verified=False,
    verification_evidence="present in captured generic help; command-specific syntax unavailable",
)
GIVE = AdminOperationMetadata("give", "give", "Give item to player", CommandRisk.MUTATING)
SEARCH_ITEMS = AdminOperationMetadata(
    "search_items", "li", "Search internal item names", CommandRisk.READ_ONLY
)
SAY = AdminOperationMetadata("say", "say", "Broadcast server message", CommandRisk.MUTATING)
MESSAGE = AdminOperationMetadata(
    "message", "pm", "Send private server message", CommandRisk.MUTATING
)
KICK = AdminOperationMetadata("kick", "kick", "Kick connected player", CommandRisk.MUTATING)
BAN = AdminOperationMetadata("ban", "ban", "Ban connected player", CommandRisk.DESTRUCTIVE)
BAN_LIST = AdminOperationMetadata("ban_list", "ban", "List active bans", CommandRisk.READ_ONLY)
UNBAN = AdminOperationMetadata("unban", "ban", "Remove active ban", CommandRisk.MUTATING)

ADMIN_OPERATIONS = {
    item.name: item
    for item in (
        GET_TIME,
        SAVE_WORLD,
        SHUTDOWN,
        GIVE,
        SEARCH_ITEMS,
        SAY,
        MESSAGE,
        KICK,
        BAN,
        BAN_LIST,
        UNBAN,
    )
}

# Compatibility alias retained for existing imports. Verification now lives per operation.
VERIFIED_OPERATIONS = ADMIN_OPERATIONS
