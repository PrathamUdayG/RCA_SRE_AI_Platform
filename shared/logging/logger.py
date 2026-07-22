"""
Purpose
-------
Structured logging utility for the AI SRE Platform.

Responsibilities
----------------
- Provide a standardized, structured logger across all platform layers.

Does NOT
---------
- Implement business logic or infrastructure network calls.
"""

import logging
import sys


def get_logger(name: str = "ai_sre_platform") -> logging.Logger:
    """
    Returns a configured structured Logger instance.

    Parameters
    ----------
    name : str
        Logger component identifier.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
