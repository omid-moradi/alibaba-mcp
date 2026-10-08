"""Structured JSON logging.

Every log record is a single JSON line on stderr, which keeps stdio clean
for the MCP wire and makes logs machine-parseable in production.

Security rule enforced by design: callers pass ``extra`` fields that are
whitelisted here. Secret values (tokens, keys, cookies) are never logged
because no code path ever passes them to the logger.
"""

import json
import logging
import sys
from datetime import UTC, datetime

_ALLOWED_EXTRA = {
    "tool",
    "provider",
    "request_id",
    "duration_ms",
    "status",
    "error_category",
    "origin",
    "destination",
    "result_count",
    "booking_id",
    "mode",
}


class JsonFormatter(logging.Formatter):
    """Format log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in _ALLOWED_EXTRA:
            value = record.__dict__.get(key)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str = "INFO") -> None:
    """Configure root logging with the JSON formatter on stderr."""
    root = logging.getLogger()
    root.setLevel(level.upper())
    if not root.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(JsonFormatter())
        root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return a logger; use together with ``configure_logging``."""
    return logging.getLogger(name)
