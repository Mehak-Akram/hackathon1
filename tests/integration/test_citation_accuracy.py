"""
Tests to verify citation accuracy across all retrieved contexts
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from backend.rag_agent.api.models.request import ChatRequest, UserPreferences, DetailLevel, ResponseFormat
from backend.rag_agent.api.models.response import RetrievedContext, ChatResponse
from backend.rag_agent.services.agent_service import agent_service
from backend.rag_agent.services.validation import validation_service


@pytest.mark.asyncio
async def test_citation_accuracy_basic():
    """Test that citations accurately reference the content in retrieved contexts"""
    chat_request = ChatRequest(
        question="What is physical AI?",
        user_preferences=UserPreferences(
            detail_level=DetailLevel.INTERMEDIATE,
            response_format=ResponseFormat.DETAILED
        )
    )

    # Create a retrieved context with specific content
    test_context = RetrievedContext(
        id="test-ctx-1",
        content="Physical AI combines robotics, machine learning, and physics to create intelligent systems that interact with the physical world. This interdisciplinary field has applications in manufacturing, healthcare, and autonomous vehicles.",
        url="https://textbook.example.com/chapter1",
        chapter="Chapter 1: Introduction to Physical AI",
        section="1.1 What is Physical AI?",
        heading_hierarchy=["Introduction", "What is Physical AI?"],
        similarity_score=0.85
    )

    # Mock the retrieval tool to return this context
    with patch.object(agent_service.textbook_agent.retrieval_tool, 'retrieve_context', new_callable=AsyncMock) as mock_retrieve:
        mock_retrieve.return_value = [test_context]

        # Mock the OpenAI client to return a response based on the context
        with patch('backend.rag_agent.agents.textbook_agent.AsyncOpenAI') as mock_client:
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message = AsyncMock()
            mock_response.choices[0].message.content = "Physical AI combines robotics, machine learning, and physics to create intelligent systems that interact with the physical world."

            mock_openai_instance = AsyncMock()
            mock_openai_instance.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_openai_instance

            # Process the request
            response = await agent_service.process_request(chat_request)

            # Validate the response
            assert response.response is not None
            assert len(response.citations) == 1

            # Validate the citation
            citation = response.citations[0]
            assert citation.source_url == "https://textbook.example.com/chapter1"
            assert citation.chapter == "Chapter 1: Introduction to Physical AI"
            assert citation.section == "1.1 What is Physical AI?"
            assert citation.similarity_score == 0.85
            assert citation.source_type == "textbook"

            # Verify that the citation refers to content that actually exists in the context
            assert "Physical AI" in test_context.content
            assert "robotics, machine learning, and physics" in test_context.content
            assert "interact with the physical world" in test_context.content

            # Validate that the citation content matches the context content
            assert citation.text_excerpt is not None
            assert citation.text_excerpt in test_context.content


@pytest.mark.asyncio
async def test_citation_accuracy_multiple_contexts():
    """Test citation accuracy when multiple contexts are retrieved"""
    chat_request = ChatRequest(
        question="How do machine learning and robotics work together in physical AI?"
    )

    # Create multiple retrieved contexts
    contexts = [
        RetrievedContext(
            id="ctx-1",
            content="Machine learning in physical AI involves training algorithms to control physical systems and robots. Deep learning techniques are particularly effective for perception tasks.",
            url="https://textbook.example.com/chapter2",
            chapter="Chapter 2: Machine Learning in Physical AI",
            section="2.1 ML Algorithms",
            heading_hierarchy=["Machine Learning", "ML Algorithms"],
            similarity_score=0.82
        ),
        RetrievedContext(
            id="ctx-2",
            content="Robotics in physical AI focuses on the design and control of physical agents that can interact with the real world. Motor control and sensor fusion are key components.",
            url="https://textbook.example.com/chapter3",
            chapter="Chapter 3: Robotics in Physical AI",
            section="3.2 Robot Control",
            heading_hierarchy=["Robotics", "Robot Control"],
            similarity_score=0.78
        ),
        RetrievedContext(
            id="ctx-3",
            content="Integration of ML and robotics requires real-time processing and robust control systems. Latency and safety are critical considerations.",
            url="https://textbook.example.com/chapter4",
            chapter="Chapter 4: Integration Challenges",
            section="4.1 System Design",
            heading_hierarchy=["Integration", "System Design"],
            similarity_score=0.75
        )
    ]

    # Mock the retrieval tool to return these contexts
    with patch.object(agent_service.textbook_agent.retrieval_tool, 'retrieve_context', new_callable=AsyncMock) as mock_retrieve:
        mock_retrieve.return_value = contexts

        # Mock the OpenAI client to return a response that combines information from multiple contexts
        with patch('backend.rag_agent.agents.textbook_agent.AsyncOpenAI') as mock_client:
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message = AsyncMock()
            mock_response.choices[0].message.content = "Machine learning and robotics work together in physical AI by using ML algorithms to control physical systems. Robotics focuses on design and control, while ML handles perception tasks. Integration requires real-time processing and safety considerations."

            mock_openai_instance = AsyncMock()
            mock_openai_instance.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_openai_instance

            # Process the request
            response = await agent_service.process_request(chat_request)

            # Validate the response
            assert response.response is not None
            assert len(response.citations) == 3  # Should have citations for all 3 contexts
            assert response.retrieved_context_count == 3

            # Validate each citation
            citations = response.citations

            # Check first citation
            assert citations[0].source_url == "https://textbook.example.com/chapter2"
            assert citations[0].chapter == "Chapter 2: Machine Learning in Physical AI"
            assert citations[0].section == "2.1 ML Algorithms"
            assert citations[0].similarity_score == 0.82
            assert citations[0].text_excerpt is not None

            # Check second citation
            assert citations[1].source_url == "https://textbook.example.com/chapter3"
            assert citations[1].chapter == "Chapter 3: Robotics in Physical AI"
            assert citations[1].section == "3.2 Robot Control"
            assert citations[1].similarity_score == 0.78
            assert citations[1].text_excerpt is not None

            # Check third citation
            assert citations[2].source_url == "https://textbook.example.com/chapter4"
            assert citations[2].chapter == "Chapter 4: Integration Challenges"
            assert citations[2].section == "4.1 System Design"
            assert citations[2].similarity_score == 0.75
            assert citations[2].text_excerpt is not None

            # Verify that each citation's excerpt matches the corresponding context
            assert citations[0].text_excerpt in contexts[0].content
            assert citations[1].text_excerpt in contexts[1].content
            assert citations[2].text_excerpt in contexts[2].content


@pytest.mark.asyncio
async def test_citation_validation_service():
    """Test the citation validation service functionality"""
    # Create a response with citations
    response = ChatResponse(
        response="Physical AI combines robotics and machine learning to create intelligent systems.",
        session_id="test-session",
        citations=[
            {
                "source_url": "https://textbook.example.com/chapter1",
                "chapter": "Chapter 1: Introduction",
                "section": "1.1 Overview",
                "similarity_score": 0.85
            }
        ],
        retrieved_context_count=1,
        response_time=0.5
    )

    # Create retrieved contexts for validation
    retrieved_contexts = [
        RetrievedContext(
            id="ctx-1",
            content="Physical AI combines robotics and machine learning to create intelligent systems.",
            url="https://textbook.example.com/chapter1",
            chapter="Chapter 1: Introduction",
            section="1.1 Overview",
            heading_hierarchy=["Introduction"],
            similarity_score=0.85
        )
    ]

    # Use the validation service to validate citations
    validation_result = validation_service.validate_response_citations(
        response=response,
        retrieved_contexts=retrieved_contexts
    )

    # Validate the validation result
    assert validation_result["valid"] is True
    assert validation_result["citation_validation"]["citation_count"] == 1
    assert validation_result["citation_validation"]["context_count"] == 1
    assert validation_result["citation_validation"]["has_citations"] is True
    assert validation_result["overall_validation"]["response_has_content"] is True
    assert validation_result["overall_validation"]["session_id_valid"] is True
    assert validation_result["overall_validation"]["response_time_positive"] is True


@pytest.mark.asyncio
async def test_citation_completeness():
    """Test that citations contain all required fields"""
    chat_request = ChatRequest(
        question="What are the key principles of physical AI?"
    )

    # Create a context with complete information
    context = RetrievedContext(
        id="complete-ctx",
        content="The key principles of physical AI include embodiment, real-time interaction, and closed-loop control between perception and action.",
        url="https://textbook.example.com/principles",
        chapter="Chapter 5: Key Principles",
        section="5.1 Fundamental Concepts",
        heading_hierarchy=["Key Principles", "Fundamental Concepts"],
        similarity_score=0.90
    )

    # Mock the retrieval tool
    with patch.object(agent_service.textbook_agent.retrieval_tool, 'retrieve_context', new_callable=AsyncMock) as mock_retrieve:
        mock_retrieve.return_value = [context]

        # Mock the OpenAI client
        with patch('backend.rag_agent.agents.textbook_agent.AsyncOpenAI') as mock_client:
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message = AsyncMock()
            mock_response.choices[0].message.content = "The key principles of physical AI include embodiment, real-time interaction, and closed-loop control between perception and action."

            mock_openai_instance = AsyncMock()
            mock_openai_instance.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_openai_instance

            # Process the request
            response = await agent_service.process_request(chat_request)

            # Validate the response
            assert response.response is not None
            assert len(response.citations) == 1

            # Validate citation completeness
            citation = response.citations[0]

            # Check required fields
            assert citation.source_url is not None and citation.source_url != ""
            assert citation.chapter is not None and citation.chapter != ""
            assert citation.section is not None and citation.section != ""

            # Check optional fields that should be populated
            assert citation.similarity_score is not None
            assert citation.source_type is not None
            assert citation.text_excerpt is not None

            # Check that the excerpt is relevant to the original content
            assert len(citation.text_excerpt) > 0
            assert citation.text_excerpt in context.content or citation.text_excerpt.startswith(context.content[:200])


@pytest.mark.asyncio
async def test_citation_source_matching():
    """Test that citations correctly match to their source contexts"""
    chat_request = ChatRequest(
        question="Compare different approaches to robot control"
    )

    # Create multiple contexts with different URLs
    contexts = [
        RetrievedContext(
            id="ctx-control",
            content="Classical control theory uses mathematical models to design controllers for robotic systems.",
            url="https://textbook.example.com/control/classical",
            chapter="Chapter 7: Control Theory",
            section="7.1 Classical Approaches",
            heading_hierarchy=["Control Theory", "Classical Approaches"],
            similarity_score=0.80
        ),
        RetrievedContext(
            id="ctx-learning",
            content="Learning-based control uses reinforcement learning and neural networks to adapt robot behavior.",
            url="https://textbook.example.com/control/learning",
            chapter="Chapter 8: Learning-Based Control",
            section="8.2 Adaptive Methods",
            heading_hierarchy=["Learning-Based Control", "Adaptive Methods"],
            similarity_score=0.85
        )
    ]

    # Mock the retrieval tool
    with patch.object(agent_service.textbook_agent.retrieval_tool, 'retrieve_context', new_callable=AsyncMock) as mock_retrieve:
        mock_retrieve.return_value = contexts

        # Mock the OpenAI client
        with patch('backend.rag_agent.agents.textbook_agent.AsyncOpenAI') as mock_client:
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message = AsyncMock()
            mock_response.choices[0].message.content = "Robot control can be approached through classical control theory using mathematical models, or through learning-based control using neural networks and reinforcement learning."

            mock_openai_instance = AsyncMock()
            mock_openai_instance.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_openai_instance

            # Process the request
            response = await agent_service.process_request(chat_request)

            # Validate the response
            assert response.response is not None
            assert len(response.citations) == 2

            # Extract and sort citations by URL to ensure they match the contexts
            citations = sorted(response.citations, key=lambda c: c.source_url)
            sorted_contexts = sorted(contexts, key=lambda c: c.url)

            # Verify each citation matches its corresponding context
            for i, (citation, context) in enumerate(zip(citations, sorted_contexts)):
                assert citation.source_url == context.url
                assert citation.chapter == context.chapter
                assert citation.section == context.section
                assert abs(citation.similarity_score - context.similarity_score) < 0.01  # Allow for small floating point differences


@pytest.mark.asyncio
async def test_citation_quality_validation():
    """Test the quality validation of citations"""
    # Create a response with citations
    response = ChatResponse(
        response="Physical AI is an important field with many applications.",
        session_id="test-session-qual",
        citations=[
            {
                "source_url": "https://textbook.example.com/chapter1",
                "chapter": "Chapter 1: Introduction",
                "section": "1.1 Overview",
                "similarity_score": 0.85,
                "confidence_score": 0.85
            }
        ],
        retrieved_context_count=1,
        response_time=0.5
    )

    # Test the quality validation service
    quality_result = validation_service.validate_citation_quality(
        citations=response.citations,
        min_confidence_score=0.5
    )

    # Validate the quality result
    assert quality_result["valid"] is True
    assert quality_result["total_citations"] == 1
    assert quality_result["citations_above_threshold"] == 1
    assert quality_result["average_confidence"] == 0.85
    assert len(quality_result["quality_issues"]) == 0

    # Test with a low confidence score
    low_quality_response = ChatResponse(
        response="Information based on uncertain sources.",
        session_id="test-session-low",
        citations=[
            {
                "source_url": "https://textbook.example.com/chapter2",
                "chapter": "Chapter 2: Uncertain Info",
                "section": "2.1 Unknown Section",
                "similarity_score": 0.3,
                "confidence_score": 0.3
            }
        ],
        retrieved_context_count=1,
        response_time=0.5
    )

    low_quality_result = validation_service.validate_citation_quality(
        citations=low_quality_response.citations,
        min_confidence_score=0.5
    )

    # With low confidence, this should be invalid
    assert low_quality_result["valid"] is False
    assert low_quality_result["citations_above_threshold"] == 0
    assert low_quality_result["quality_issues"]


if __name__ == "__main__":
    pytest.main([__file__])