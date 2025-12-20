"""
Integration test for agent response.
Tests that the agent can send a message and receive a response from Gemini.
"""
import pytest
from src.agents.gemini_agent import GeminiAgent


@pytest.mark.asyncio
async def test_agent_response_generation():
    """
    Test that the agent can send a message and receive a response.
    """
    # Initialize the agent
    agent = GeminiAgent()

    # Test with a simple message
    test_message = "Hello, how are you?"
    response = await agent.run(test_message)

    # Verify that we got a response
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0

    # Verify that the response is from the AI (not empty or placeholder)
    assert not response.isspace()


@pytest.mark.asyncio
async def test_agent_multiple_interactions():
    """
    Test that the agent can handle multiple interactions.
    """
    agent = GeminiAgent()

    # First interaction
    response1 = await agent.run("What is 2+2?")
    assert response1 is not None and len(response1) > 0

    # Second interaction
    response2 = await agent.run("What is the capital of France?")
    assert response2 is not None and len(response2) > 0

    # Both responses should be valid
    assert isinstance(response1, str)
    assert isinstance(response2, str)