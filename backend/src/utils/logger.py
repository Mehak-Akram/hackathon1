"""
Logging configuration module for the Gemini AI Agent.
Sets up verbose logging as required and disables tracing.
"""
import logging
import sys


def setup_logger(name="gemini_agent", level=logging.DEBUG):
    """
    Set up a logger with verbose logging configuration.
    Tracing is disabled as required by the specification.
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent adding multiple handlers if logger already exists
    if logger.handlers:
        return logger

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(console_handler)

    # Disable tracing (as required by the specification)
    # This is accomplished by not enabling any distributed tracing systems

    return logger


# Global logger instance
logger = setup_logger()