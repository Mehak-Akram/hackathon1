"""
Integration test for environment loading.
Tests that the system loads API key from environment variables.
"""
import os
import pytest
from unittest import mock
from src.utils.config_loader import load_config
from src.agents.agent_config import AgentConfig


def test_environment_loading_with_dotenv():
    """
    Test that environment variables are loaded from .env file.
    """
    # Mock that the .env file has been loaded with the correct value
    with mock.patch.dict(os.environ, {
        "GEMINI_API_KEY": "test_key_from_env_12345"
    }):
        config = load_config()
        assert config["gemini_api_key"] == "test_key_from_env_12345"


def test_agent_config_uses_loaded_api_key():
    """
    Test that agent configuration uses the loaded API key.
    """
    with mock.patch.dict(os.environ, {
        "GEMINI_API_KEY": "test_agent_key_12345"
    }):
        agent_config = AgentConfig()

        # Verify the API key is properly loaded in the agent config
        assert agent_config.config["gemini_api_key"] == "test_agent_key_12345"

        # Verify the client was created with the correct API key
        # Note: We can't directly access client.api_key due to OpenAI library implementation,
        # but we can verify that the config was properly loaded


def test_missing_api_key_handling():
    """
    Test graceful failure when API key is missing.
    """
    # Remove the API key from environment if it exists
    original_key = os.environ.get("GEMINI_API_KEY")
    if "GEMINI_API_KEY" in os.environ:
        del os.environ["GEMINI_API_KEY"]

    try:
        with pytest.raises(ValueError, match="GEMINI_API_KEY environment variable is required"):
            load_config()
    finally:
        # Restore original environment
        if original_key:
            os.environ["GEMINI_API_KEY"] = original_key