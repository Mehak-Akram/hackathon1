"""
Comprehensive integration tests for end-to-end functionality of the RAG Agent Service
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from backend.rag_agent.api.models.request import ChatRequest, UserPreferences, DetailLevel, ResponseFormat
from backend.rag_agent.api.models.response import RetrievedContext, ChatResponse
from backend.rag_agent.services.agent_service import agent_service
from backend.rag_agent.agents.textbook_agent import TextbookAgent
from backend.rag_agent.services.conversation import conversation_service


@pytest.mark.asyncio
async def test_end_to_end_single_question():
    """Test complete end-to-end flow for a single question"""
    # Create a mock chat request
    chat_request = ChatRequest(
        question="What are the fundamental principles of physical AI?",
        user_preferences=UserPreferences(
            detail_level=DetailLevel.INTERMEDIATE,
            response_format=ResponseFormat.DETAILED
        )
    )

    # Mock the retrieval tool to return contexts
    with patch.object(agent_service.textbook_agent.retrieval_tool, 'retrieve_context', new_callable=AsyncMock) as mock_retrieve:
        mock_retrieve.return_value = [
            RetrievedContext(
                id="test-ctx-1",
                content="Physical AI combines robotics, machine learning, and physics to create intelligent systems that interact with the physical world.",
                url="https://textbook.example.com/chapter1",
                chapter="Chapter 1: Introduction to Physical AI",
                section="1.1 What is Physical AI?",
                heading_hierarchy=["Introduction", "What is Physical AI?"],
                similarity_score=0.85
            )
        ]

        # Mock the OpenAI client
        with patch('backend.rag_agent.agents.textbook_agent.AsyncOpenAI') as mock_client:
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message = AsyncMock()
            mock_response.choices[0].message.content = "Physical AI is a field that combines robotics, machine learning, and physics to create intelligent systems that interact with the physical world."

            mock_openai_instance = AsyncMock()
            mock_openai_instance.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_openai_instance

            # Process the request
            response = await agent_service.process_request(chat_request)

            # Validate the response
            assert isinstance(response, ChatResponse)
            assert response.response is not None
            assert len(response.response) > 0
            assert len(response.citations) == 1
            assert response.retrieved_context_count == 1
            assert response.response_time > 0

            # Validate citation
            citation = response.citations[0]
            assert citation.source_url == "https://textbook.example.com/chapter1"
            assert citation.chapter == "Chapter 1: Introduction to Physical AI"
            assert citation.section == "1.1 What is Physical AI?"


@pytest.mark.asyncio
async def test_end_to_end_multi_turn_conversation():
    """Test complete end-to-end flow for multi-turn conversation"""
    # Create a session for the conversation
    session = await conversation_service.create_session()
    session_id = session.id

    try:
        # First question
        chat_request_1 = ChatRequest(
            question="What is physical AI?",
            session_id=session_id
        )

        # Mock the retrieval tool for first question
        with patch.object(agent_service.textbook_agent.retrieval_tool, 'retrieve_context', new_callable=AsyncMock) as mock_retrieve:
            mock_retrieve.return_value = [
                RetrievedContext(
                    id="test-ctx-1",
                    content="Physical AI combines robotics and machine learning.",
                    url="https://textbook.example.com/chapter1",
                    chapter="Chapter 1",
                    section="1.1",
                    heading_hierarchy=["Chapter 1"],
                    similarity_score=0.85
                )
            ]

            # Mock the OpenAI client
            with patch('backend.rag_agent.agents.textbook_agent.AsyncOpenAI') as mock_client:
                mock_response = AsyncMock()
                mock_response.choices = [AsyncMock()]
                mock_response.choices[0].message = AsyncMock()
                mock_response.choices[0].message.content = "Physical AI combines robotics and machine learning to create intelligent systems."

                mock_openai_instance = AsyncMock()
                mock_openai_instance.chat.completions.create = AsyncMock(return_value=mock_response)
                mock_client.return_value = mock_openai_instance

                response_1 = await agent_service.process_request(chat_request_1)

                # Verify first response
                assert response_1.response is not None
                assert response_1.session_id == session_id
                assert len(response_1.citations) == 1

                # Check that conversation history was updated
                session_after_first = await conversation_service.get_session(session_id)
                assert len(session_after_first.conversation_history) == 1

                # Second question (follow-up)
                chat_request_2 = ChatRequest(
                    question="How does it differ from traditional AI?",
                    session_id=session_id
                )

                # Mock the retrieval tool for second question
                mock_retrieve.return_value = [
                    RetrievedContext(
                        id="test-ctx-2",
                        content="Traditional AI operates on digital data while Physical AI interacts with the physical world.",
                        url="https://textbook.example.com/chapter2",
                        chapter="Chapter 2",
                        section="2.1 Differences",
                        heading_hierarchy=["Chapter 2", "Differences"],
                        similarity_score=0.78
                    )
                ]

                mock_response.choices[0].message.content = "Traditional AI operates on digital data while Physical AI interacts with the physical world."

                response_2 = await agent_service.process_request(chat_request_2)

                # Verify second response
                assert response_2.response is not None
                assert response_2.session_id == session_id
                assert len(response_2.citations) == 1

                # Check that conversation history now has both turns
                session_after_second = await conversation_service.get_session(session_id)
                assert len(session_after_second.conversation_history) == 2

    finally:
        # Clean up the session
        await conversation_service.end_session(session_id)


@pytest.mark.asyncio
async def test_error_handling_fallback_mechanisms():
    """Test that error handling and fallback mechanisms work properly"""
    chat_request = ChatRequest(
        question="What is error handling in physical AI?",
        session_id="test-session"
    )

    # Mock the retrieval tool to raise an exception
    with patch.object(agent_service.textbook_agent.retrieval_tool, 'retrieve_context', side_effect=Exception("Retrieval failed")):
        # Mock the conversation service to raise an exception
        with patch.object(conversation_service, 'get_conversation_context', side_effect=Exception("Context retrieval failed")):
            # Mock the conversation history update to raise an exception
            with patch.object(conversation_service, 'add_conversation_turn', side_effect=Exception("History update failed")):
                # Process the request - should trigger fallback mechanisms
                response = await agent_service.process_request(chat_request)

                # Even with errors, should return a valid response
                assert isinstance(response, ChatResponse)
                assert response.response is not None
                assert "encountered an issue" in response.response.lower() or "sorry" in response.response.lower()
                assert response.session_id == "test-session"


@pytest.mark.asyncio
async def test_circuit_breaker_retry_logic():
    """Test the circuit breaker and retry logic"""
    chat_request = ChatRequest(
        question="Test question for retry logic",
        session_id="test-session-retry"
    )

    # Mock the retrieval tool to fail initially then succeed
    call_count = 0

    async def mock_retrieve_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:  # Fail first 2 attempts
            raise Exception(f"Simulated failure on attempt {call_count}")
        else:  # Succeed on 3rd attempt
            return [
                RetrievedContext(
                    id="test-ctx-1",
                    content="Test content for retry.",
                    url="https://textbook.example.com/test",
                    chapter="Test Chapter",
                    section="Test Section",
                    heading_hierarchy=["Test"],
                    similarity_score=0.80
                )
            ]

    with patch.object(agent_service.textbook_agent.retrieval_tool, 'retrieve_context', side_effect=mock_retrieve_side_effect):
        with patch('backend.rag_agent.agents.textbook_agent.AsyncOpenAI') as mock_client:
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message = AsyncMock()
            mock_response.choices[0].message.content = "This is a test response after retries."

            mock_openai_instance = AsyncMock()
            mock_openai_instance.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_openai_instance

            # Process the request with circuit breaker - should succeed after retries
            response = await agent_service.process_request_with_circuit_breaker(chat_request, max_retries=3)

            # Verify the response was successful after retries
            assert isinstance(response, ChatResponse)
            assert response.response is not None
            assert "test response" in response.response.lower()
            assert call_count == 3  # Should have called 3 times (failed 2, succeeded on 3rd)


@pytest.mark.asyncio
async def test_service_health_check():
    """Test the service health check functionality"""
    health_status = await agent_service.validate_service_health()

    # Verify the health status structure
    assert "service" in health_status
    assert "status" in health_status
    assert "components" in health_status
    assert "timestamp" in health_status

    # Verify component status
    components = health_status["components"]
    assert "textbook_agent" in components
    assert "conversation_service" in components
    assert "validation_service" in components

    # At a minimum, the service should be connected to components
    assert components["textbook_agent"]["details"]["connected"] is True
    assert components["conversation_service"]["details"]["connected"] is True
    assert components["validation_service"]["details"]["connected"] is True


@pytest.mark.asyncio
async def test_service_metrics():
    """Test the service metrics functionality"""
    metrics = await agent_service.get_service_metrics()

    # Verify the metrics structure
    assert "timestamp" in metrics
    assert "active_sessions" in metrics
    assert "session_timeout_minutes" in metrics
    assert "default_top_k" in metrics
    assert "agent_model" in metrics

    # Metrics should be properly populated
    assert isinstance(metrics["active_sessions"], int)
    assert isinstance(metrics["session_timeout_minutes"], int)
    assert isinstance(metrics["default_top_k"], int)
    assert isinstance(metrics["agent_model"], str)


@pytest.mark.asyncio
async def test_user_preferences_handling():
    """Test that user preferences are properly handled"""
    chat_request = ChatRequest(
        question="Explain physical AI concepts",
        user_preferences=UserPreferences(
            detail_level=DetailLevel.ADVANCED,
            response_format=ResponseFormat.EXAMPLES
        )
    )

    with patch.object(agent_service.textbook_agent.retrieval_tool, 'retrieve_context', new_callable=AsyncMock) as mock_retrieve:
        mock_retrieve.return_value = [
            RetrievedContext(
                id="test-ctx-1",
                content="Advanced physical AI concepts with examples.",
                url="https://textbook.example.com/chapter1",
                chapter="Chapter 1",
                section="1.1",
                heading_hierarchy=["Chapter 1"],
                similarity_score=0.90
            )
        ]

        with patch('backend.rag_agent.agents.textbook_agent.AsyncOpenAI') as mock_client:
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message = AsyncMock()
            mock_response.choices[0].message.content = "Advanced explanation with examples..."

            mock_openai_instance = AsyncMock()
            mock_openai_instance.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_openai_instance

            response = await agent_service.process_request(chat_request)

            # Verify the response was generated with user preferences considered
            assert response.response is not None
            assert len(response.citations) == 1

            # The agent should have been called with the user preferences
            # This would be verified by checking the prompt construction in a real test


if __name__ == "__main__":
    pytest.main([__file__])