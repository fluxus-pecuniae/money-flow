"""Structured logging configuration."""

from __future__ import annotations

import logging
import sys

import structlog
from pythonjsonlogger.json import JsonFormatter

from core.config.settings import LoggingConfig
from core.security import redact_structured_log_event


def redact_structlog_event(_, __, event_dict):
    """Structlog processor that redacts obvious secret-bearing fields."""

    return redact_structured_log_event(event_dict)


def configure_logging(config: LoggingConfig) -> None:
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(config.level)

    handler = logging.StreamHandler(sys.stdout)
    if config.json_logs:
        handler.setFormatter(
            JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    root.addHandler(handler)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.dict_tracebacks,
            redact_structlog_event,
            structlog.processors.JSONRenderer()
            if config.json_logs
            else structlog.dev.ConsoleRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str):
    return structlog.get_logger(name)
