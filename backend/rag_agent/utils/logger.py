"""
Enhanced logging utilities for the RAG Agent Service
"""
import logging
import sys
from typing import Optional
from contextvars import ContextVar

# Context variable to track request ID
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)


class RequestIdFilter(logging.Filter):
    """
    Logging filter to add request ID to log records
    """
    def filter(self, record):
        request_id = request_id_var.get()
        record.request_id = request_id or 'N/A'
        return True


def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Set up a logger with the specified name and level
    """
    logger = logging.getLogger(name)

    # Use the level from settings if not provided
    if level is None:
        try:
            from backend.rag_agent.config.settings import settings
            level = settings.log_level
        except ImportError:
            # Fallback to environment variable or default
            import os
            level = os.getenv('LOG_LEVEL', 'INFO')

    logger.setLevel(getattr(logging, level.upper()))

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(RequestIdFilter())
    logger.addHandler(console_handler)

    # File handler
    file_handler = logging.FileHandler('rag_agent.log', mode='a')
    file_handler.setFormatter(formatter)
    file_handler.addFilter(RequestIdFilter())
    logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name
    """
    return setup_logger(name)


# Create a global logger instance
logger = get_logger(__name__)