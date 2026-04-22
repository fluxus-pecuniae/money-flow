"""Structured logging configuration."""

from __future__ import annotations

import logging
import sys

import structlog
from pythonjsonlogger.json import JsonFormatter

from core.config.settings import LoggingConfig


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
