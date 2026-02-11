"""
Shortlist — Structured Logging

JSON-structured logging for production observability.
Sanitizes sensitive data from log output.
"""

import logging
import json
import sys
from datetime import datetime, timezone
from typing import Any

from app.config import get_settings


# Fields that must NEVER appear in logs
SENSITIVE_FIELDS = frozenset({
    "password", "token", "secret", "api_key", "apikey",
    "authorization", "cookie", "session", "credit_card",
    "ssn", "private_key", "supabase_key", "groq_api_key",
    "openai_api_key",
})


def _redact(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively redact sensitive fields from log data."""
    redacted = {}
    for key, value in data.items():
        if key.lower() in SENSITIVE_FIELDS:
            redacted[key] = "***REDACTED***"
        elif isinstance(value, dict):
            redacted[key] = _redact(value)
        else:
            redacted[key] = value
    return redacted


class JSONFormatter(logging.Formatter):
    """
    Outputs structured JSON logs.
    Ideal for log aggregation (CloudWatch, Datadog, etc.)
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Include exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Include extra fields (redacted)
        if hasattr(record, "extra_data"):
            log_entry["data"] = _redact(record.extra_data)

        return json.dumps(log_entry, default=str)


def setup_logging() -> logging.Logger:
    """Configure application-wide logging."""
    settings = get_settings()

    logger = logging.getLogger("shortlist")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    if settings.ENVIRONMENT == "production":
        handler.setFormatter(JSONFormatter())
    else:
        # Human-readable format for development
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d — %(message)s",
                datefmt="%H:%M:%S",
            )
        )

    logger.addHandler(handler)
    return logger


def get_logger(name: str = "shortlist") -> logging.Logger:
    """Get a child logger with the given name."""
    return logging.getLogger(f"shortlist.{name}")
