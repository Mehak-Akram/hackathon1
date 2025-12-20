"""
Configuration loader module for the Gemini AI Agent.
Handles loading of environment variables and API keys.
"""
import os
from dotenv import load_dotenv


def load_config():
    """
    Load environment variables from .env file.
    Returns a dictionary with configuration values.
    """
    # Load environment variables from .env file
    load_dotenv()

    # Get the GEMINI_API_KEY from environment variables
    gemini_api_key = os.getenv("GEMINI_API_KEY")

    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY environment variable is required but not set")

    config = {
        "gemini_api_key": gemini_api_key,
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "model": "gemini-2.0-flash"
    }

    return config