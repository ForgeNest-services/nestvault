"""Structured logging setup for NestVault using loguru."""

import sys

from loguru import logger


def setup_logging(level: str = "INFO") -> None:
    """Configure loguru for NestVault.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logger.remove()

    logger.add(
        sys.stdout,
        format="[{time:YYYY-MM-DDTHH:mm:ss.SSS}Z] [{level}] [{extra[component]}] {message}",
        level=level.upper(),
        colorize=True,
    )


def get_logger(component: str):
    """Get a logger bound with component context.

    Args:
        component: Name of the component (e.g., 'backup.postgres', 'storage.s3')

    Returns:
        Logger bound with component context
    """
    return logger.bind(component=component)
