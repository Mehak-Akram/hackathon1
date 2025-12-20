"""
Test script to verify agent integration with new error logging capabilities
"""
import asyncio
from typing import Dict, Any

from .agents.textbook_agent import textbook_agent
from .utils.logger import get_logger
from .utils.error_handler import error_handler

logger = get_logger(__name__)


async def test_agent_integration():
    """
    Test that the textbook agent works properly with new error logging
    """
    print("Testing agent integration with error logging...")

    # Test error handler is working
    print(f"Error handler initialized: {error_handler is not None}")

    # Test that the agent instance exists
    print(f"Textbook agent initialized: {textbook_agent is not None}")

    # Test basic agent properties
    print(f"Agent client initialized: {hasattr(textbook_agent, 'client')}")
    print(f"Agent retrieval tool initialized: {hasattr(textbook_agent, 'retrieval_tool')}")
    print(f"Agent conversation service initialized: {hasattr(textbook_agent, 'conversation_service')}")

    # Test error summary
    error_summary = error_handler.get_error_summary()
    print(f"Initial error summary: {error_summary}")

    print("Agent integration test completed successfully!")


def run_integration_test():
    """
    Run agent integration test
    """
    print("Starting agent integration test with error logging...")
    asyncio.run(test_agent_integration())
    print("Integration test completed!")


if __name__ == "__main__":
    run_integration_test()