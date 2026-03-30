from __future__ import annotations

import logging
from typing import Optional

_LOGGER_CONFIGURED = False


def configure_logging(level: int | str = logging.INFO) -> None:
    """Configure root logger once for console output."""
    global _LOGGER_CONFIGURED
    if _LOGGER_CONFIGURED:
        return

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    _LOGGER_CONFIGURED = True


def get_logger(name: str, level: int | str = logging.INFO) -> logging.Logger:
    """Return a logger configured for console use."""
    configure_logging(level)
    return logging.getLogger(name)
