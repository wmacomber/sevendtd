"""Small structured-logging helpers with a strict safe-field boundary."""

import logging
from collections.abc import Mapping
from typing import Final

LOGGER_NAME: Final = "sevendtd"

SAFE_FIELDS: Final = frozenset(
    {
        "resource",
        "endpoint",
        "method",
        "status_code",
        "latency_ms",
        "attempt",
        "retry_delay",
        "event_type",
        "exception_category",
        "operation",
        "risk",
    }
)


def get_logger() -> logging.Logger:
    return logging.getLogger(LOGGER_NAME)


def safe_extra(fields: Mapping[str, object]) -> dict[str, object]:
    """Discard unapproved fields before they enter a log record."""

    return {key: value for key, value in fields.items() if key in SAFE_FIELDS}
