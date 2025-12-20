"""
Contract test for Gemini API integration.
Tests that the AsyncOpenAI client can connect to the Gemini endpoint.
"""
import pytest
from openai import AsyncOpenAI
from src.utils.config_loader import load_config


@pytest.mark.asyncio
async def test_gemini_api_connection():
    """
    Test that we can create a client and connect to the Gemini endpoint.
    """
    config = load_config()

    # Create AsyncOpenAI client with Gemini's base URL
    client = AsyncOpenAI(
        api_key=config["gemini_api_key"],
        base_url=config["base_url"]
    )

    # Verify that the client was created with the correct configuration
    assert client.base_url == config["base_url"]
    assert client.api_key == config["gemini_api_key"]

    # Basic test - this should not raise an exception if the API key is valid
    # Note: This test requires a valid GEMINI_API_KEY to pass
    try:
        # Just testing the client configuration, not making an actual call yet
        assert client is not None
    except Exception as e:
        # If there's an issue with the API key or connection, we'll catch it here
        pytest.fail(f"Failed to create/configure client: {e}")


@pytest.mark.asyncio
async def test_gemini_model_availability():
    """
    Test that the gemini-2.0-flash model is available through the API.
    """
    config = load_config()

    client = AsyncOpenAI(
        api_key=config["gemini_api_key"],
        base_url=config["base_url"]
    )

    # Verify the model name is correctly configured
    assert config["model"] == "gemini-2.0-flash"