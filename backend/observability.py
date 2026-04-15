from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any


_STANDARD_RECORD_FIELDS = set(logging.makeLogRecord({}).__dict__.keys())
_CONFIGURED = False


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        event = getattr(record, "event", None)
        if event:
            payload["event"] = event

        for key, value in record.__dict__.items():
            if key in _STANDARD_RECORD_FIELDS or key.startswith("_"):
                continue
            payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging() -> logging.Logger:
    global _CONFIGURED

    logger = logging.getLogger("mystic")
    if _CONFIGURED:
        return logger

    level_name = os.getenv("LOG_LEVEL", "INFO").strip().upper() or "INFO"
    level = getattr(logging, level_name, logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())

    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False

    _CONFIGURED = True
    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    configure_logging()
    if not name:
        return logging.getLogger("mystic")
    if name.startswith("mystic"):
        return logging.getLogger(name)
    return logging.getLogger(f"mystic.{name}")


def log_event(
    logger: logging.Logger,
    level: int,
    message: str,
    *,
    event: str,
    exc_info: Any = None,
    **fields: Any,
) -> None:
    logger.log(level, message, extra={"event": event, **fields}, exc_info=exc_info)
