"""
Logging configuration and utilities.

Provides structured logging with file rotation and request tracking.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from loguru import logger
from ..core.config import get_settings


def setup_logging(log_file: Optional[Path] = None):
    """
    Configure logging for the application.

    Args:
        log_file: Optional path to log file. Uses settings default if not provided.
    """
    settings = get_settings()
    log_file = log_file or settings.log_file

    # Remove default logger
    logger.remove()

    # Add console logger
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True
    )

    # Add file logger with rotation
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.log_level,
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        compression="zip"
    )

    logger.info(f"Logging initialized - Level: {settings.log_level}, File: {log_file}")


def get_logger(name: str) -> logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logger.bind(name=name)


class RequestLogger:
    """Context manager for logging request processing."""

    def __init__(self, request_id: str, operation: str):
        """
        Initialize request logger.

        Args:
            request_id: Unique request identifier
            operation: Operation being performed
        """
        self.request_id = request_id
        self.operation = operation
        self.logger = logger.bind(request_id=request_id)

    def __enter__(self):
        self.logger.info(f"Starting {self.operation}")
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.logger.error(f"{self.operation} failed: {exc_val}")
        else:
            self.logger.info(f"{self.operation} completed successfully")
        return False
