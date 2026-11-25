"""Utility functions and logging setup for SmartSched AI."""

import logging
import os
import sys
from typing import Optional

DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s:%(lineno)d - %(message)s"


def setup_logger(
    name: str = "smartsched",
    level: int = logging.INFO,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """Configures and returns a standardized logger instance.

    Args:
        name: Logger name.
        level: Logging level (e.g. logging.INFO, logging.DEBUG).
        log_file: Optional path to append log outputs.

    Returns:
        logging.Logger: Configured logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers if already initialized
    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
        logger.addHandler(console_handler)

        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
            logger.addHandler(file_handler)

    return logger
