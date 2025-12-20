"""
Gemini AI Agent implementation.
Uses the OpenAI Agent SDK but connects to Google Gemini's free tier model.
"""
from ..utils.logger import logger
from .agent_config import AgentConfig


class GeminiAgent:
    """
    AI agent that uses the OpenAI Agent SDK but connects to Google Gemini's endpoint.
    """
    def __init__(self):
        self.config = AgentConfig()
        self.client = self.config.client
        self.model = self.config.model

        # Verify that tracing is disabled as required
        assert self.config.tracing_enabled is False, "Tracing must be disabled as per requirements"

        logger.info(f"Initialized GeminiAgent with model: {self.model}")
        logger.info(f"Tracing disabled: {self.config.tracing_enabled}")
        logger.info(f"Logging level: {self.config.logging_level}")

    async def run(self, message: str):
        """
        Run the agent with the given message and return the response.
        """
        logger.debug(f"Agent run called with message: {message}")
        logger.info(f"Running agent with message: {message[:50]}...")

        try:
            # Make a request to the Gemini endpoint using the OpenAI-compatible API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": message}],
                temperature=0.7
            )

            # Extract the response content
            result = response.choices[0].message.content

            logger.debug(f"Full response received: {result}")
            logger.info(f"Received response from Gemini: {result[:50]}...")
            return result

        except Exception as e:
            logger.error(f"Error during agent run: {str(e)}")
            raise