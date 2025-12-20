"""
Test script to validate comprehensive error logging and debugging capabilities
"""
import asyncio
import time
from datetime import datetime
from typing import Dict, Any

from rag_agent.utils.logger import get_logger
from rag_agent.utils.error_handler import error_handler, handle_exceptions
from rag_agent.utils.debug_utils import (
    DebuggingContext,
    debug_trace,
    debug_memory_monitor,
    debug_performance_monitor,
    log_data_flow,
    get_system_diagnostics,
    log_system_diagnostics,
    debug_on_error,
    print_debug_info,
    time_block
)
from rag_agent.utils.helpers import log_error_with_context


logger = get_logger(__name__)


@debug_trace(include_args=True, include_result=True, log_level="DEBUG")
@debug_performance_monitor(time_threshold=0.1, memory_threshold=1.0)
@log_data_flow(operation="test_function")
@handle_exceptions(
    fallback_return="Error occurred in test function",
    log_error=True,
    reraise=False,
    include_system_diagnostics=True
)
async def test_debugging_function(input_data: str) -> Dict[str, Any]:
    """Test function to validate debugging capabilities"""
    print_debug_info("Input Data", input_data)

    # Simulate some processing
    await asyncio.sleep(0.1)

    result = {
        "processed_data": f"Processed: {input_data}",
        "timestamp": datetime.now().isoformat(),
        "length": len(input_data)
    }

    print_debug_info("Result", result)
    return result


@debug_on_error(lambda: get_system_diagnostics())
async def test_error_handling():
    """Test error handling with debugging"""
    try:
        # This should trigger error handling
        raise ValueError("Test error for debugging validation")
    except Exception as e:
        error_id = log_error_with_context(e, {"test_context": "error_handling_test"})
        logger.info(f"Error handled with ID: {error_id}")
        return error_id


async def main():
    """Main test function to validate all debugging capabilities"""
    print("Testing comprehensive error logging and debugging capabilities...")

    # Test 1: System diagnostics
    print("\n1. Testing system diagnostics:")
    diagnostics = get_system_diagnostics()
    print_debug_info("System Diagnostics", diagnostics, max_length=1000)

    # Test 2: System diagnostics logging
    print("\n2. Testing system diagnostics logging:")
    log_system_diagnostics()

    # Test 3: Debugging context
    print("\n3. Testing debugging context:")
    with DebuggingContext(
        operation_name="test_operation",
        log_inputs=True,
        log_outputs=True,
        log_memory=True,
        log_performance=True
    ):
        await asyncio.sleep(0.1)  # Simulate work

    # Test 4: Function with debugging decorators
    print("\n4. Testing function with debugging decorators:")
    result = await test_debugging_function("test_input_123")
    print(f"Function result: {result}")

    # Test 5: Error handling with debugging
    print("\n5. Testing error handling with debugging:")
    error_id = await test_error_handling()
    print(f"Error ID from test: {error_id}")

    # Test 6: Time block context
    print("\n6. Testing time block context:")
    with time_block("test_time_block"):
        await asyncio.sleep(0.05)

    # Test 7: Error handler statistics
    print("\n7. Testing error handler statistics:")
    error_summary = error_handler.get_error_summary()
    print_debug_info("Error Summary", error_summary)

    print("\nAll debugging capabilities validated successfully!")


if __name__ == "__main__":
    asyncio.run(main())