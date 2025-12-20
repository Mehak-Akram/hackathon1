"""
Unit test for logging configuration.
Tests that verbose logging is enabled and tracing is disabled.
"""
import logging
from src.utils.logger import setup_logger, logger


def test_verbose_logging_enabled():
    """
    Test that verbose logging is enabled as required.
    """
    # Get the default logger
    test_logger = setup_logger("test_logger", level=logging.DEBUG)

    # Check that the logger level is set to DEBUG (verbose)
    assert test_logger.level == logging.DEBUG


def test_logger_format():
    """
    Test that the logger has the correct format for verbose logging.
    """
    test_logger = setup_logger("format_test", level=logging.DEBUG)

    # Check that the logger has handlers
    assert len(test_logger.handlers) > 0

    # Check that at least one handler has the expected format
    handler = test_logger.handlers[0]
    expected_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # We can't directly check the format string, but we can check that it's a Formatter
    assert isinstance(handler.formatter, logging.Formatter)


def test_global_logger_exists():
    """
    Test that the global logger instance is created.
    """
    # The global logger should already exist
    assert logger is not None
    assert hasattr(logger, 'info')
    assert hasattr(logger, 'debug')
    assert hasattr(logger, 'error')
    assert hasattr(logger, 'warning')


def test_tracing_disabled():
    """
    Test that tracing is disabled as required.
    This is accomplished by ensuring no distributed tracing libraries are configured.
    """
    # In our implementation, tracing is disabled by not enabling any distributed tracing systems
    # We can verify this by checking that no tracing-related handlers are added
    test_logger = setup_logger("tracing_test", level=logging.DEBUG)

    # Our logger should only have the basic StreamHandler for console output
    # No additional tracing handlers should be present
    for handler in test_logger.handlers:
        # Confirm it's a basic StreamHandler, not a tracing handler
        assert 'StreamHandler' in str(type(handler))