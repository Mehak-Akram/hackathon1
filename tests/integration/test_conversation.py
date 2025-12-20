"""
Integration tests for multi-turn conversations with follow-up questions
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from backend.rag_agent.api.models.request import ChatRequest
from backend.rag_agent.api.models.response import RetrievedContext
from backend.rag_agent.agents.textbook_agent import TextbookAgent
from backend.rag_agent.services.conversation import conversation_service


@pytest.mark.asyncio
async def test_multi_turn_conversation():
    """Test multi-turn conversations with follow-up questions"""
    agent = TextbookAgent()

    # Create a new session
    session = await conversation_service.create_session()
    session_id = session.id

    try:
        # Mock the retrieval tool to return contexts
        with patch.object(agent.retrieval_tool, 'retrieve_context', new_callable=AsyncMock) as mock_retrieve:
            # First, mock for the initial question
            mock_retrieve.return_value = [
                RetrievedContext(
                    id="test-ctx-1",
                    content="Physical AI combines robotics, machine learning, and physics to create intelligent systems that interact with the textbook content.",
                    url="https://textbook.example.com/chapter1",
                    chapter="Chapter 1: Introduction to Physical AI",
                    section="1.1 What is Physical AI?",
                    heading_hierarchy=["Introduction", "What is Physical AI?"],
                    similarity_score=0.85
                )
            ]

            # Also mock the OpenAI client
            with patch('backend.rag_agent.agents.textbook_agent.AsyncOpenAI') as mock_client:
                mock_response = AsyncMock()
                mock_response.choices = [AsyncMock()]
                mock_response.choices[0].message = AsyncMock()
                mock_response.choices[0].message.content = "Physical AI is a field that combines robotics, machine learning, and physics to create intelligent systems."

                mock_openai_instance = AsyncMock()
                mock_openai_instance.chat.completions.create = AsyncMock(return_value=mock_response)
                mock_client.return_value = mock_openai_instance

                # First question
                response1 = await agent.answer_question(
                    question="What is physical AI?",
                    session_id=session_id
                )

                assert response1.response is not None
                assert "Physical AI" in response1.response

                # Verify that conversation history was updated
                session = await conversation_service.get_session(session_id)
                assert len(session.conversation_history) == 1
                assert session.conversation_history[0]["question"] == "What is physical AI?"

                # Follow-up question
                mock_retrieve.return_value = [
                    RetrievedContext(
                        id="test-ctx-2",
                        content="Machine learning in Physical AI involves training algorithms to control physical systems and robots.",
                        url="https://textbook.example.com/chapter2",
                        chapter="Chapter 2: Machine Learning in Physical AI",
                        section="2.1 ML Algorithms",
                        heading_hierarchy=["Machine Learning", "ML Algorithms"],
                        similarity_score=0.78
                    )
                ]

                mock_response.choices[0].message.content = "In the context of Physical AI, machine learning involves training algorithms to control physical systems and robots."

                response2 = await agent.answer_question(
                    question="How does machine learning fit in?",
                    session_id=session_id
                )

                assert response2.response is not None
                assert len(response2.response) > 0

                # Verify that conversation history now has both turns
                session = await conversation_service.get_session(session_id)
                assert len(session.conversation_history) == 2
                assert session.conversation_history[0]["question"] == "What is physical AI?"
                assert session.conversation_history[1]["question"] == "How does machine learning fit in?"

    finally:
        # Clean up the session
        await conversation_service.end_session(session_id)


@pytest.mark.asyncio
async def test_conversation_context_inclusion():
    """Test that conversation context is properly included in prompts"""
    agent = TextbookAgent()

    # Create a new session
    session = await conversation_service.create_session()
    session_id = session.id

    try:
        # Add some conversation history manually
        await conversation_service.add_conversation_turn(
            session_id,
            "What is physical AI?",
            "Physical AI combines robotics, machine learning, and physics."
        )

        # Mock the retrieval tool
        with patch.object(agent.retrieval_tool, 'retrieve_context', new_callable=AsyncMock) as mock_retrieve:
            mock_retrieve.return_value = [
                RetrievedContext(
                    id="test-ctx-1",
                    content="Robots in Physical AI are controlled by intelligent algorithms.",
                    url="https://textbook.example.com/chapter3",
                    chapter="Chapter 3: Robotics in Physical AI",
                    section="3.1 Robot Control",
                    heading_hierarchy=["Robotics", "Robot Control"],
                    similarity_score=0.82
                )
            ]

            # Mock the OpenAI client to capture the messages sent
            with patch('backend.rag_agent.agents.textbook_agent.AsyncOpenAI') as mock_client:
                mock_response = AsyncMock()
                mock_response.choices = [AsyncMock()]
                mock_response.choices[0].message = AsyncMock()
                mock_response.choices[0].message.content = "Robots in Physical AI are controlled by intelligent algorithms."

                mock_openai_instance = AsyncMock()
                call_capture = []

                async def capture_messages(*args, **kwargs):
                    call_capture.append(kwargs.get('messages', []))
                    return mock_response

                mock_openai_instance.chat.completions.create = capture_messages
                mock_client.return_value = mock_openai_instance

                # Ask a follow-up question
                await agent.answer_question(
                    question="What about the robots?",
                    session_id=session_id
                )

                # Verify that the conversation history was included in the messages
                assert len(call_capture) == 1
                messages = call_capture[0]

                # Find the system message that should contain the conversation history
                system_messages_with_history = [
                    msg for msg in messages
                    if msg.get('role') == 'system' and 'Previous conversation:' in msg.get('content', '')
                ]

                assert len(system_messages_with_history) >= 1
                history_content = system_messages_with_history[0]['content']
                assert "Q1: What is physical AI?" in history_content
                assert "A1: Physical AI combines robotics, machine learning, and physics." in history_content

    finally:
        # Clean up the session
        await conversation_service.end_session(session_id)


@pytest.mark.asyncio
async def test_conversation_service_operations():
    """Test basic conversation service operations"""
    # Create a session
    session = await conversation_service.create_session(user_id="test-user", metadata={"test": True})
    session_id = session.id

    try:
        # Verify session was created
        retrieved_session = await conversation_service.get_session(session_id)
        assert retrieved_session is not None
        assert retrieved_session.user_id == "test-user"
        assert retrieved_session.metadata["test"] is True
        assert len(retrieved_session.conversation_history) == 0

        # Add a conversation turn
        success = await conversation_service.add_conversation_turn(
            session_id,
            "Test question",
            "Test response"
        )
        assert success is True

        # Verify the turn was added
        updated_session = await conversation_service.get_session(session_id)
        assert len(updated_session.conversation_history) == 1
        assert updated_session.conversation_history[0]["question"] == "Test question"
        assert updated_session.conversation_history[0]["response"] == "Test response"

        # Get conversation context
        context = await conversation_service.get_conversation_context(session_id, max_turns=5)
        assert len(context) == 1
        assert context[0]["question"] == "Test question"

    finally:
        # Clean up
        success = await conversation_service.end_session(session_id)
        assert success is True

        # Verify session was removed
        removed_session = await conversation_service.get_session(session_id)
        assert removed_session is None


if __name__ == "__main__":
    pytest.main([__file__])