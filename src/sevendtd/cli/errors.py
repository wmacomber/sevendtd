"""Project exception to stable process-exit mapping."""

from sevendtd.exceptions import (
    SevenDTDAPIError,
    SevenDTDAuthenticationError,
    SevenDTDConfigurationError,
    SevenDTDConnectionError,
    SevenDTDError,
    SevenDTDInvalidResponseError,
    SevenDTDTimeoutError,
)


def exit_code(error: SevenDTDError) -> int:
    if isinstance(error, (SevenDTDConfigurationError, SevenDTDAuthenticationError)):
        return 3
    if isinstance(error, (SevenDTDConnectionError, SevenDTDTimeoutError)):
        return 4
    if isinstance(error, (SevenDTDAPIError, SevenDTDInvalidResponseError)):
        return 5
    return 5
