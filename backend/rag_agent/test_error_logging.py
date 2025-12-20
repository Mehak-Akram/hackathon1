"""
Test script for error logging and debugging capabilities
"""
import asyncio
import time
from typing import Dict, Any

from .utils.error_handler import error_handler, handle_exceptions, debug_context, log_function_call
from .utils.helpers import log_error_with_context, safe_execute
from .utils.logger import get_logger

logger = get_logger(__name__)


async def test_error_logging():
    """
    Test comprehensive error logging capabilities
    """
    print("Testing error logging capabilities...")

    # Test basic error logging
    try:
        raise ValueError("This is a test error for logging")
    except Exception as e:
        context = {"test_function": "test_error_logging", "test_param": "value1"}
        error_id = log_error_with_context(e, context)
        print(f"Logged error with ID: {error_id}")

    # Test error handler
    try:
        raise RuntimeError("Test runtime error")
    except Exception as e:
        error_id = error_handler.log_error(e, {"component": "test_component"})
        print(f"Handled error with ID: {error_id}")

    # Test handle_exceptions decorator
    @handle_exceptions(fallback_return="fallback_result", log_error=True)
    async def problematic_function():
        raise Exception("This is an intentional error for testing")

    result = await problematic_function()
    print(f"Function returned: {result}")

    # Test safe_execute decorator
    @safe_execute
    def another_problematic_function():
        raise ValueError("Another intentional error")

    result2 = another_problematic_function()
    print(f"Safe function returned: {result2}")

    # Test function call logging
    @log_function_call(include_args=True, include_result=True)
    async def sample_function(x: int, y: str = "default"):
        await asyncio.sleep(0.1)  # Simulate some work
        return f"Result: {x}, {y}"

    result3 = await sample_function(42, "test")
    print(f"Sample function returned: {result3}")

    # Test debug context
    with debug_context("sample_operation", log_level="INFO"):
        await asyncio.sleep(0.05)
        print("Inside debug context")

    # Get error summary
    error_summary = error_handler.get_error_summary()
    print(f"Error summary: {error_summary}")

    print("Error logging tests completed successfully!")


def run_tests():
    """
    Run all error logging tests
    """
    print("Starting comprehensive error logging tests...")
    asyncio.run(test_error_logging())
    print("All tests completed!")


if __name__ == "__main__":
    run_tests()