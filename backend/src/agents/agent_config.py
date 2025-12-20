"""
Agent configuration module for the Gemini AI Agent.
Configures the AsyncOpenAI client to use Gemini's OpenAI-compatible endpoint.
"""
from openai import AsyncOpenAI
from ..utils.config_loader import load_config


def create_gemini_client():
    """
    Create and return an AsyncOpenAI client configured to use Gemini's endpoint.
    """
    config = load_config()

    # Create AsyncOpenAI client with Gemini's base URL
    client = AsyncOpenAI(
        api_key=config["gemini_api_key"],
        base_url=config["base_url"]
    )

    return client


class AgentConfig:
    """
    Configuration class for the Gemini Agent.
    """
    def __init__(self):
        self.config = load_config()
        self.client = create_gemini_client()
        self.model = self.config["model"]

        # Ensure tracing is disabled as required
        self.tracing_enabled = False
        self.logging_level = "verbose"