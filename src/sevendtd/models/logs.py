"""SSE and typed log-event models."""

from dataclasses import dataclass
from datetime import UTC, datetime

from pydantic import AwareDatetime, Field

from sevendtd.models.common import ProtocolModel


@dataclass(frozen=True, slots=True)
class SSEFrame:
    event: str
    data: str
    event_id: str | None = None
    retry: int | None = None


class LogLinePayload(ProtocolModel):
    id: int
    msg: str
    type: str
    trace: str | None
    isotime: AwareDatetime
    uptime: str


class BaseLogEvent(ProtocolModel):
    event_type: str
    event_id: str | None = None
    raw_data: str
    received_at: AwareDatetime = Field(default_factory=lambda: datetime.now(UTC))


class LogLineEvent(BaseLogEvent):
    payload: LogLinePayload


class UnknownLogEvent(BaseLogEvent):
    pass


class MalformedLogEvent(BaseLogEvent):
    error: str


@dataclass(frozen=True, slots=True)
class ReconnectPolicy:
    max_attempts: int | None = 5
    initial_delay: float = 0.5
    maximum_delay: float = 30.0
    factor: float = 2.0
    jitter_ratio: float = 0.2

    def __post_init__(self) -> None:
        if self.max_attempts is not None and self.max_attempts < 0:
            raise ValueError("max_attempts must be non-negative or None")
        if self.initial_delay < 0 or self.maximum_delay < 0:
            raise ValueError("delays must be non-negative")
        if self.factor < 1:
            raise ValueError("factor must be at least one")
        if not 0 <= self.jitter_ratio <= 1:
            raise ValueError("jitter_ratio must be between zero and one")

    def delay_for(self, attempt: int, jitter: float = 0.0) -> float:
        base = min(self.initial_delay * self.factor ** max(0, attempt - 1), self.maximum_delay)
        return max(0.0, base * (1 + jitter * self.jitter_ratio))
