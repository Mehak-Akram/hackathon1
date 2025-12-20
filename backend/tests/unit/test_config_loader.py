"""
Unit test for config_loader module.
Tests that environment variables are loaded correctly.
"""
import os
import tempfile
from unittest import mock
from src.utils.config_loader import load_config


def test_load_config_with_valid_env():
    """
    Test that config is loaded correctly when environment variables are set.
    """
    with mock.patch.dict(os.environ, {
        "GEMINI_API_KEY": "test_api_key_12345"
    }):
        config = load_config()

        assert config["gemini_api_key"] == "test_api_key_12345"
        assert config["base_url"] == "https://generativelanguage.googleapis.com/v1beta/openai/"
        assert config["model"] == "gemini-2.0-flash"


def test_load_config_missing_api_key():
    """
    Test that an error is raised when GEMINI_API_KEY is not set.
    """
    # Temporarily clear the environment variable if it exists
    original_key = os.environ.get("GEMINI_API_KEY")
    if "GEMINI_API_KEY" in os.environ:
        del os.environ["GEMINI_API_KEY"]

    try:
        # This should raise a ValueError
        load_config()
        assert False, "Expected ValueError when GEMINI_API_KEY is not set"
    except ValueError as e:
        assert "GEMINI_API_KEY environment variable is required" in str(e)
    finally:
        # Restore original environment
        if original_key:
            os.environ["GEMINI_API_KEY"] = original_key


def test_config_values():
    """
    Test that all expected config values are present.
    """
    with mock.patch.dict(os.environ, {
        "GEMINI_API_KEY": "test_api_key_12345"
    }):
        config = load_config()

        # Check that all required keys exist
        assert "gemini_api_key" in config
        assert "base_url" in config
        assert "model" in config

        # Check that values are correct
        assert config["base_url"] == "https://generativelanguage.googleapis.com/v1beta/openai/"
        assert config["model"] == "gemini-2.0-flash"