"""
Integration tests for the complete agent service with diverse textbook queries
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from backend.rag_agent.api.models.request import ChatRequest, UserPreferences, DetailLevel, ResponseFormat
from backend.rag_agent.api.models.response import RetrievedContext, Citation
from backend.rag_agent.services.agent_service import agent_service


@pytest.mark.asyncio
async def test_agent_service_basic_functionality():
    """Test basic functionality of the complete agent service"""
    # Create a simple chat request
    chat_request = ChatRequest(
        question="What is physical AI?",
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
            assert response.response is not None
            assert "Physical AI" in response.response
            assert len(response.citations) == 1
            assert response.retrieved_context_count == 1
            assert response.response_time > 0

            # Validate citation
            citation = response.citations[0]
            assert citation.source_url == "https://textbook.example.com/chapter1"
            assert citation.chapter == "Chapter 1: Introduction to Physical AI"


@pytest.mark.asyncio
async def test_agent_service_diverse_questions():
    """Test the agent service with diverse textbook queries"""
    test_questions = [
        "What are the fundamental principles of physical AI?",
        "How does machine learning apply to robotics?",
        "Explain the concept of embodied intelligence.",
        "What is the difference between classical AI and physical AI?",
        "How do sensors and actuators work in physical AI systems?"
    ]

    for question in test_questions:
        chat_request = ChatRequest(question=question)

        # Mock the retrieval tool to return contexts
        with patch.object(agent_service.textbook_agent.retrieval_tool, 'retrieve_context', new_callable=AsyncMock) as mock_retrieve:
            mock_retrieve.return_value = [
                RetrievedContext(
                    id=f"test-ctx-{hash(question) % 1000}",
                    content=f"Content related to {question} that is found in the textbook.",
                    url=f"https://textbook.example.com/search?q={hash(question)}",
                    chapter="Various chapters",
                    section="Various sections",
                    heading_hierarchy=["Related Topic"],
                    similarity_score=0.75
                )
            ]

            # Mock the OpenAI client
            with patch('backend.rag_agent.agents.textbook_agent.AsyncOpenAI') as mock_client:
                mock_response = AsyncMock()
                mock_response.choices = [AsyncMock()]
                mock_response.choices[0].message = AsyncMock()
                mock_response.choices[0].message.content = f"Based on the textbook, {question} is explained as a fundamental concept in physical AI."

                mock_openai_instance = AsyncMock()
                mock_openai_instance.chat.completions.create = AsyncMock(return_value=mock_response)
                mock_client.return_value = mock_openai_instance

                # Process the request
                response = await agent_service.process_request(chat_request)

                # Validate the response
                assert response.response is not None
                assert len(response.response) > 0
                assert len(response.citations) == 1
                assert response.retrieved_context_count == 1
                assert response.response_time > 0


@pytest.mark.asyncio
async def test_agent_service_with_session():
    """Test the agent service with session management"""
    # Create a session first
    session = await agent_service.conversation_service.create_session()
    session_id = session.id

    try:
        # First question
        chat_request_1 = ChatRequest(
            question="What is physical AI?",
            session_id=session_id
        )

        # Mock the retrieval tool
        with patch.object(agent_service.textbook_agent.retrieval_tool, 'retrieve_context', new_callable=AsyncMock) as mock_retrieve:
            mock_retrieve.return_value = [
                RetrievedContext(
                    id="test-ctx-1",
                    content="Physical AI combines robotics, machine learning, and physics.",
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
                mock_response.choices[0].message.content = "Physical AI combines robotics, machine learning, and physics."

                mock_openai_instance = AsyncMock()
                mock_openai_instance.chat.completions.create = AsyncMock(return_value=mock_response)
                mock_client.return_value = mock_openai_instance

                # Process the first request
                response_1 = await agent_service.process_request(chat_request_1)

                # Validate first response
                assert response_1.response is not None
                assert response_1.session_id == session_id
                assert len(response_1.citations) == 1

                # Verify that conversation history was updated
                updated_session = await agent_service.conversation_service.get_session(session_id)
                assert len(updated_session.conversation_history) == 1
                assert updated_session.conversation_history[0]["question"] == "What is physical AI?"

                # Second question (follow-up)
                chat_request_2 = ChatRequest(
                    question="How does it differ from traditional AI?",
                    session_id=session_id
                )

                # Update mock for second question
                mock_retrieve.return_value = [
                    RetrievedContext(
                        id="test-ctx-2",
                        content="Traditional AI operates on digital data while Physical AI interacts with the physical world.",
                        url="https://textbook.example.com/chapter2",
                        chapter="Chapter 2",
                        section="2.1",
                        heading_hierarchy=["Chapter 2"],
                        similarity_score=0.78
                    )
                ]

                mock_response.choices[0].message.content = "Traditional AI operates on digital data while Physical AI interacts with the physical world."

                # Process the second request
                response_2 = await agent_service.process_request(chat_request_2)

                # Validate second response
                assert response_2.response is not None
                assert response_2.session_id == session_id
                assert len(response_2.citations) == 1

                # Verify that conversation history now has both turns
                final_session = await agent_service.conversation_service.get_session(session_id)
                assert len(final_session.conversation_history) == 2
                assert final_session.conversation_history[0]["question"] == "What is physical AI?"
                assert final_session.conversation_history[1]["question"] == "How does it differ from traditional AI?"

    finally:
        # Clean up the session
        await agent_service.conversation_service.end_session(session_id)


@pytest.mark.asyncio
async def test_agent_service_user_preferences():
    """Test the agent service with different user preferences"""
    preferences_test_cases = [
        {
            "detail_level": DetailLevel.BASIC,
            "response_format": ResponseFormat.CONCISE,
            "expected_style": "basic and concise"
        },
        {
            "detail_level": DetailLevel.INTERMEDIATE,
            "response_format": ResponseFormat.DETAILED,
            "expected_style": "intermediate and detailed"
        },
        {
            "detail_level": DetailLevel.ADVANCED,
            "response_format": ResponseFormat.EXAMPLES,
            "expected_style": "advanced with examples"
        }
    ]

    for test_case in preferences_test_cases:
        chat_request = ChatRequest(
            question="Explain neural networks in physical AI",
            user_preferences=UserPreferences(
                detail_level=test_case["detail_level"],
                response_format=test_case["response_format"]
            )
        )

        # Mock the retrieval tool
        with patch.object(agent_service.textbook_agent.retrieval_tool, 'retrieve_context', new_callable=AsyncMock) as mock_retrieve:
            mock_retrieve.return_value = [
                RetrievedContext(
                    id="test-ctx-1",
                    content="Neural networks in physical AI are used for control and perception.",
                    url="https://textbook.example.com/chapter3",
                    chapter="Chapter 3: Neural Networks",
                    section="3.1 Introduction",
                    heading_hierarchy=["Neural Networks", "Introduction"],
                    similarity_score=0.82
                )
            ]

            # Mock the OpenAI client
            with patch('backend.rag_agent.agents.textbook_agent.AsyncOpenAI') as mock_client:
                mock_response = AsyncMock()
                mock_response.choices = [AsyncMock()]
                mock_response.choices[0].message = AsyncMock()
                mock_response.choices[0].message.content = f"Neural networks explanation tailored for {test_case['expected_style']}."

                mock_openai_instance = AsyncMock()
                mock_openai_instance.chat.completions.create = AsyncMock(return_value=mock_response)
                mock_client.return_value = mock_openai_instance

                # Process the request
                response = await agent_service.process_request(chat_request)

                # Validate the response
                assert response.response is not None
                assert len(response.response) > 0
                assert len(response.citations) == 1
                assert response.retrieved_context_count == 1
                assert response.response_time > 0


@pytest.mark.asyncio
async def test_agent_service_error_handling():
    """Test error handling in the agent service"""
    chat_request = ChatRequest(
        question="What happens when there are errors?",
        session_id="test-session-error"
    )

    # Test when retrieval tool fails
    with patch.object(agent_service.textbook_agent.retrieval_tool, 'retrieve_context', side_effect=Exception("Retrieval failed")):
        # Mock the OpenAI client to return a response despite the error
        with patch('backend.rag_agent.agents.textbook_agent.AsyncOpenAI') as mock_client:
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message = AsyncMock()
            mock_response.choices[0].message.content = "I'm sorry, but I encountered an issue while processing your request. Please try again later."

            mock_openai_instance = AsyncMock()
            mock_openai_instance.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_openai_instance

            # Process the request - should handle error gracefully
            response = await agent_service.process_request_with_circuit_breaker(chat_request, max_retries=1)

            # Validate that a response was still returned despite the error
            assert response.response is not None
            assert "encountered an issue" in response.response.lower() or "sorry" in response.response.lower()


@pytest.mark.asyncio
async def test_agent_service_performance_tracking():
    """Test that the agent service properly tracks performance metrics"""
    chat_request = ChatRequest(
        question="Test performance tracking",
        user_preferences=UserPreferences(
            detail_level=DetailLevel.BASIC,
            response_format=ResponseFormat.CONCISE
        )
    )

    # Mock the retrieval tool
    with patch.object(agent_service.textbook_agent.retrieval_tool, 'retrieve_context', new_callable=AsyncMock) as mock_retrieve:
        mock_retrieve.return_value = [
            RetrievedContext(
                id="perf-test-ctx",
                content="Performance testing content.",
                url="https://textbook.example.com/performance",
                chapter="Performance Testing",
                section="Test Section",
                heading_hierarchy=["Performance", "Testing"],
                similarity_score=0.90
            )
        ]

        # Mock the OpenAI client
        with patch('backend.rag_agent.agents.textbook_agent.AsyncOpenAI') as mock_client:
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message = AsyncMock()
            mock_response.choices[0].message.content = "This is a test response for performance tracking."

            mock_openai_instance = AsyncMock()
            mock_openai_instance.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_openai_instance

            # Process the request with detailed logging
            processing_log = await agent_service.process_request_with_detailed_logging(chat_request)

            # Validate the processing log
            assert "request_id" in processing_log
            assert "steps" in processing_log
            assert "total_time" in processing_log
            assert "result" in processing_log
            assert processing_log["total_time"] > 0
            assert len(processing_log["steps"]) > 0

            # Validate the result
            result = processing_log["result"]
            assert "response_length" in result
            assert "citation_count" in result
            assert "response_time" in result
            assert result["citation_count"] == 1


if __name__ == "__main__":
    pytest.main([__file__])