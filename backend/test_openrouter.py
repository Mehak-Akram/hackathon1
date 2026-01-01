#!/usr/bin/env python3
"""
Test script to verify OpenRouter integration works correctly
"""
import asyncio
import os
from rag_agent.agents.textbook_agent import TextbookAgent
from rag_agent.config.settings import settings

async def test_openrouter_connection():
    """Test that the OpenRouter client can be initialized and used"""
    print("Testing OpenRouter integration...")

    # Create an instance of the textbook agent
    agent = TextbookAgent()

    print(f"Agent model: {agent.model}")
    print(f"Client type: {type(agent.client)}")

    # Check if we have the OpenRouter API key
    if not settings.openrouter_api_key:
        print("WARNING: OPENROUTER_API_KEY not found in environment. Using fallback.")
        if not settings.openai_api_key:
            print("ERROR: No API keys configured. Please set either OPENROUTER_API_KEY or OPENAI_API_KEY in your .env file.")
            return False

    # Try a simple test with a basic question
    test_question = "What is 2+2? This is a simple test."

    try:
        print(f"Testing with question: {test_question}")
        response = await agent.answer_question(test_question)
        print(f"Response received: {response.response[:100]}...")
        print(f"Response time: {response.response_time:.2f}s")
        print(f"Citations: {len(response.citations)}")
        return True
    except Exception as e:
        print(f"Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    print("Starting OpenRouter integration test...")
    success = asyncio.run(test_openrouter_connection())

    if success:
        print("\nSUCCESS: OpenRouter integration test completed successfully!")
    else:
        print("\nFAILED: OpenRouter integration test failed!")
        exit(1)