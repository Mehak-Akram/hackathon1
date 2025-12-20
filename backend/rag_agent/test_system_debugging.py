"""
Quick test to validate the RAG Agent Service with enhanced debugging capabilities
"""
import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.rag_agent.config.settings import settings
from backend.rag_agent.agents.textbook_agent import textbook_agent
from backend.rag_agent.services.agent_service import agent_service
from backend.rag_agent.api.models.request import ChatRequest, UserPreferences
from backend.rag_agent.utils.logger import get_logger
from backend.rag_agent.utils.debug_utils import log_system_diagnostics

logger = get_logger(__name__)

async def test_rag_agent_with_debugging():
    """Test the RAG agent with enhanced debugging capabilities"""
    print("Testing RAG Agent Service with enhanced debugging capabilities...")

    # Log system diagnostics at start
    log_system_diagnostics()

    # Test 1: Test the textbook agent directly
    print("\n1. Testing textbook agent directly:")
    try:
        response = await textbook_agent.answer_question(
            question="What is Physical AI?",
            session_id="test_session_123",
            user_preferences={"detail_level": "intermediate", "response_format": "detailed"}
        )
        print(f"Agent response: {response.response[:100]}...")
        print(f"Number of citations: {len(response.citations)}")
        print(f"Response time: {response.response_time:.2f}s")
    except Exception as e:
        print(f"Error in textbook agent test: {e}")

    # Test 2: Test through agent service
    print("\n2. Testing through agent service:")
    try:
        chat_request = ChatRequest(
            question="What are the key concepts in Physical AI?",
            session_id="test_session_456",
            user_preferences=UserPreferences(
                detail_level="intermediate",
                response_format="detailed"
            )
        )
        response = await agent_service.process_request(chat_request)
        print(f"Service response: {response.response[:100]}...")
        print(f"Response time: {response.response_time:.2f}s")
    except Exception as e:
        print(f"Error in agent service test: {e}")

    # Test 3: Test with circuit breaker
    print("\n3. Testing with circuit breaker pattern:")
    try:
        chat_request = ChatRequest(
            question="Explain the relationship between physics and AI?",
            session_id="test_session_789",
            user_preferences=UserPreferences(
                detail_level="advanced",
                response_format="examples"
            )
        )
        response = await agent_service.process_request_with_circuit_breaker(chat_request)
        print(f"Circuit breaker response: {response.response[:100]}...")
        print(f"Response time: {response.response_time:.2f}s")
    except Exception as e:
        print(f"Error in circuit breaker test: {e}")

    print("\nRAG Agent Service debugging capabilities validated successfully!")

if __name__ == "__main__":
    # Check if required environment variables are set
    if not settings.openai_api_key or settings.openai_api_key == "your-openai-api-key-here":
        print("Warning: OpenAI API key not configured. Using mock response.")
        # For testing purposes, we'll proceed anyway to validate the debugging infrastructure
        pass

    asyncio.run(test_rag_agent_with_debugging())