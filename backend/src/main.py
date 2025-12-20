"""
Main entry point for the Gemini AI Agent.
"""
import asyncio
import sys
import argparse
from .agents.gemini_agent import GeminiAgent
from .utils.logger import logger


def main():
    """
    Main function to demonstrate the Gemini AI Agent.
    """
    parser = argparse.ArgumentParser(description='Gemini AI Agent')
    parser.add_argument('--server', action='store_true', help='Run as a FastAPI server')
    args = parser.parse_args()

    if args.server:
        # Import and run the FastAPI server
        import uvicorn
        from .server import app

        logger.info("Starting Gemini AI Agent as FastAPI server...")
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        logger.info("Starting Gemini AI Agent in CLI mode...")

        try:
            # Initialize the agent
            agent = GeminiAgent()
            logger.info("GeminiAgent initialized successfully")

            # Example usage
            message = "Hello, this is a test message from the Gemini AI Agent."
            logger.info(f"Sending message: {message}")

            response = asyncio.run(agent.run(message))
            logger.info(f"Received response: {response}")

            print(f"Response: {response}")

        except Exception as e:
            logger.error(f"Error in main execution: {str(e)}")
            sys.exit(1)


if __name__ == "__main__":
    main()