"""Project-owned, secret-safe exception hierarchy."""

from collections.abc import Sequence
from dataclasses import dataclass


class SevenDTDError(Exception):
    """Base error for every public library failure."""


class SevenDTDConfigurationError(SevenDTDError):
    pass


class SevenDTDTransportError(SevenDTDError):
    pass


class SevenDTDConnectionError(SevenDTDTransportError):
    pass


class SevenDTDTimeoutError(SevenDTDTransportError):
    pass


class SevenDTDAuthenticationError(SevenDTDError):
    def __init__(self, endpoint: str, status_code: int) -> None:
        self.endpoint = endpoint
        self.status_code = status_code
        super().__init__(f"authentication failed for {endpoint} (HTTP {status_code})")


class SevenDTDAPIError(SevenDTDError):
    def __init__(self, endpoint: str, status_code: int) -> None:
        self.endpoint = endpoint
        self.status_code = status_code
        super().__init__(f"upstream request failed for {endpoint} (HTTP {status_code})")


class SevenDTDInvalidResponseError(SevenDTDError):
    pass


class SevenDTDCommandError(SevenDTDError):
    pass


class SevenDTDSSEError(SevenDTDError):
    pass


class SevenDTDMapTileError(SevenDTDError):
    pass


@dataclass(frozen=True, slots=True)
class SnapshotErrorDetail:
    component: str
    error_type: str
    message: str


class SevenDTDSnapshotError(SevenDTDError):
    def __init__(self, failures: Sequence[SnapshotErrorDetail]) -> None:
        self.failures = tuple(failures)
        super().__init__(f"snapshot failed in {len(self.failures)} component(s)")
