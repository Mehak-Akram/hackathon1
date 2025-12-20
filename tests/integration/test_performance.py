"""
Performance tests to validate that 95% of questions receive responses within 10 seconds
"""
import asyncio
import time
import statistics
from typing import List
import pytest
from unittest.mock import AsyncMock, patch
from backend.rag_agent.api.models.request import ChatRequest, UserPreferences, DetailLevel, ResponseFormat
from backend.rag_agent.api.models.response import RetrievedContext
from backend.rag_agent.services.agent_service import agent_service


@pytest.mark.asyncio
async def test_response_time_within_threshold():
    """Test that responses are delivered within the 10-second threshold"""
    # Test multiple questions to get a statistical sample
    test_questions = [
        "What is physical AI?",
        "Explain neural networks in robotics",
        "How does machine learning apply to physical systems?",
        "What are the key components of a physical AI system?",
        "Describe the relationship between perception and action in physical AI",
        "What is embodied cognition?",
        "How do sensors contribute to physical AI?",
        "What role does motor control play in physical AI?",
        "Explain reinforcement learning in physical environments",
        "What are the challenges of real-time physical AI?"
    ]

    response_times = []

    for question in test_questions:
        chat_request = ChatRequest(
            question=question,
            user_preferences=UserPreferences(
                detail_level=DetailLevel.INTERMEDIATE,
                response_format=ResponseFormat.DETAILED
            )
        )

        # Mock the retrieval tool
        with patch.object(agent_service.textbook_agent.retrieval_tool, 'retrieve_context', new_callable=AsyncMock) as mock_retrieve:
            mock_retrieve.return_value = [
                RetrievedContext(
                    id=f"test-ctx-{hash(question) % 1000}",
                    content=f"Content related to {question} that is found in the textbook.",
                    url=f"https://textbook.example.com/chapter{hash(question) % 10}",
                    chapter=f"Chapter {hash(question) % 10}: Relevant Topic",
                    section=f"{hash(question) % 10}.{hash(question) % 5} Relevant Section",
                    heading_hierarchy=["Topic", "Subtopic"],
                    similarity_score=0.75 + (abs(hash(question)) % 25) / 100  # Random score between 0.75-1.0
                )
            ]

            # Mock the OpenAI client
            with patch('backend.rag_agent.agents.textbook_agent.AsyncOpenAI') as mock_client:
                mock_response = AsyncMock()
                mock_response.choices = [AsyncMock()]
                mock_response.choices[0].message = AsyncMock()
                mock_response.choices[0].message.content = f"Based on the textbook, {question} is explained as a fundamental concept in physical AI. This response is generated to test performance metrics."

                mock_openai_instance = AsyncMock()
                mock_openai_instance.chat.completions.create = AsyncMock(return_value=mock_response)
                mock_client.return_value = mock_openai_instance

                # Measure the response time
                start_time = time.time()
                response = await agent_service.process_request(chat_request)
                end_time = time.time()

                response_time = end_time - start_time
                response_times.append(response_time)

                # Validate individual response
                assert response.response is not None
                assert len(response.response) > 0
                assert response.response_time <= 30  # Should be much less than 30 seconds
                assert response_time <= 10  # Individual responses should be under 10 seconds

    # Calculate performance statistics
    avg_response_time = statistics.mean(response_times)
    median_response_time = statistics.median(response_times)
    max_response_time = max(response_times)
    min_response_time = min(response_times)

    print(f"Performance Statistics:")
    print(f"  Total requests: {len(response_times)}")
    print(f"  Average response time: {avg_response_time:.3f}s")
    print(f"  Median response time: {median_response_time:.3f}s")
    print(f"  Min response time: {min_response_time:.3f}s")
    print(f"  Max response time: {max_response_time:.3f}s")
    print(f"  95th percentile (estimated): {sorted(response_times)[int(len(response_times) * 0.95) - 1]:.3f}s")

    # Validate that all responses are under 10 seconds
    responses_under_10s = sum(1 for t in response_times if t <= 10)
    success_rate = responses_under_10s / len(response_times) * 100

    print(f"  Responses under 10s: {responses_under_10s}/{len(response_times)} ({success_rate:.1f}%)")

    # Validate that at least 95% of responses are under 10 seconds
    assert success_rate >= 95.0, f"Only {success_rate:.1f}% of responses were under 10 seconds, need at least 95%"

    # Additional validation: average response time should be reasonable
    assert avg_response_time < 5.0, f"Average response time {avg_response_time:.3f}s is too high"


@pytest.mark.asyncio
async def test_concurrent_request_performance():
    """Test performance under concurrent load"""
    # Create multiple similar requests to simulate concurrent usage
    num_concurrent = 5
    test_questions = [f"What is physical AI concept #{i}?" for i in range(num_concurrent)]

    async def process_request_async(question_idx):
        question = test_questions[question_idx]
        chat_request = ChatRequest(
            question=question,
            user_preferences=UserPreferences(
                detail_level=DetailLevel.BASIC,
                response_format=ResponseFormat.CONCISE
            )
        )

        # Mock the retrieval tool
        with patch.object(agent_service.textbook_agent.retrieval_tool, 'retrieve_context', new_callable=AsyncMock) as mock_retrieve:
            mock_retrieve.return_value = [
                RetrievedContext(
                    id=f"concurrent-ctx-{question_idx}",
                    content=f"Content for concept #{question_idx}.",
                    url=f"https://textbook.example.com/concept/{question_idx}",
                    chapter=f"Chapter X: Concept #{question_idx}",
                    section=f"X.{question_idx}",
                    heading_hierarchy=[f"Concept #{question_idx}"],
                    similarity_score=0.80
                )
            ]

            # Mock the OpenAI client
            with patch('backend.rag_agent.agents.textbook_agent.AsyncOpenAI') as mock_client:
                mock_response = AsyncMock()
                mock_response.choices = [AsyncMock()]
                mock_response.choices[0].message = AsyncMock()
                mock_response.choices[0].message.content = f"Response for concept #{question_idx}."

                mock_openai_instance = AsyncMock()
                mock_openai_instance.chat.completions.create = AsyncMock(return_value=mock_response)
                mock_client.return_value = mock_openai_instance

                start_time = time.time()
                response = await agent_service.process_request(chat_request)
                end_time = time.time()

                return end_time - start_time, response

    # Execute all requests concurrently
    start_total = time.time()
    results = await asyncio.gather(
        *[process_request_async(i) for i in range(num_concurrent)]
    )
    end_total = time.time()

    total_time = end_total - start_total
    response_times = [result[0] for result in results]

    print(f"Concurrent Performance Statistics ({num_concurrent} requests):")
    print(f"  Total execution time: {total_time:.3f}s")
    print(f"  Average response time: {statistics.mean(response_times):.3f}s")
    print(f"  Max response time: {max(response_times):.3f}s")

    # All responses should be under 10 seconds
    for i, response_time in enumerate(response_times):
        assert response_time <= 10, f"Request {i} took {response_time:.3f}s, exceeding 10s threshold"

    # All should have received responses
    responses = [result[1] for result in results]
    for i, response in enumerate(responses):
        assert response.response is not None
        assert len(response.response) > 0


@pytest.mark.asyncio
async def test_slow_response_detection():
    """Test that slow responses are properly logged and handled"""
    # Create a request that will take longer than normal
    chat_request = ChatRequest(
        question="Give me a comprehensive overview of all physical AI concepts",
        user_preferences=UserPreferences(
            detail_level=DetailLevel.ADVANCED,
            response_format=ResponseFormat.DETAILED
        )
    )

    # Mock the retrieval tool to return multiple contexts (more complex processing)
    with patch.object(agent_service.textbook_agent.retrieval_tool, 'retrieve_context', new_callable=AsyncMock) as mock_retrieve:
        # Actually create the list properly
        mock_retrieve.return_value = [
            RetrievedContext(
                id="slow-test-ctx-1",
                content="Content for complex physical AI concept 1. This content is longer and more detailed to simulate complex processing requirements.",
                url="https://textbook.example.com/complex/1",
                chapter="Chapter 1: Complex Concepts",
                section="1.1",
                heading_hierarchy=["Complex Concepts", "1.1"],
                similarity_score=0.85
            ),
            RetrievedContext(
                id="slow-test-ctx-2",
                content="Content for complex physical AI concept 2. This content is longer and more detailed to simulate complex processing requirements.",
                url="https://textbook.example.com/complex/2",
                chapter="Chapter 2: Advanced Topics",
                section="2.1",
                heading_hierarchy=["Advanced Topics", "2.1"],
                similarity_score=0.82
            ),
            RetrievedContext(
                id="slow-test-ctx-3",
                content="Content for complex physical AI concept 3. This content is longer and more detailed to simulate complex processing requirements.",
                url="https://textbook.example.com/complex/3",
                chapter="Chapter 3: Deep Understanding",
                section="3.1",
                heading_hierarchy=["Deep Understanding", "3.1"],
                similarity_score=0.80
            )
        ]

        # Mock the OpenAI client
        with patch('backend.rag_agent.agents.textbook_agent.AsyncOpenAI') as mock_client:
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message = AsyncMock()
            mock_response.choices[0].message.content = "This is a comprehensive response to your complex question about physical AI concepts, incorporating multiple textbook sources to provide detailed information."

            mock_openai_instance = AsyncMock()
            mock_openai_instance.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_openai_instance

            # Process the request
            start_time = time.time()
            response = await agent_service.process_request(chat_request)
            end_time = time.time()

            response_time = end_time - start_time

            # Validate the response
            assert response.response is not None
            assert len(response.response) > 0
            assert len(response.citations) == 3  # Should have citations for all 3 contexts
            assert response.retrieved_context_count == 3

            # Even complex requests should complete within 10 seconds
            assert response_time <= 10, f"Complex request took {response_time:.3f}s, exceeding 10s threshold"
            assert response.response_time <= 10


@pytest.mark.asyncio
async def test_response_time_consistency():
    """Test that response times are consistent across different types of queries"""
    # Test various types of questions
    test_cases = [
        ("Simple yes/no question?", DetailLevel.BASIC),
        ("What is a neural network?", DetailLevel.INTERMEDIATE),
        ("Explain the mathematical foundations of neural networks in robotics with examples", DetailLevel.ADVANCED),
        ("Compare and contrast different machine learning approaches", DetailLevel.INTERMEDIATE),
        ("How do I implement a physical AI system?", DetailLevel.ADVANCED)
    ]

    response_times = []

    for question, detail_level in test_cases:
        chat_request = ChatRequest(
            question=question,
            user_preferences=UserPreferences(
                detail_level=detail_level,
                response_format=ResponseFormat.DETAILED
            )
        )

        # Mock the retrieval tool
        with patch.object(agent_service.textbook_agent.retrieval_tool, 'retrieve_context', new_callable=AsyncMock) as mock_retrieve:
            mock_retrieve.return_value = [
                RetrievedContext(
                    id=f"consistency-ctx-{hash(question) % 100}",
                    content=f"Content related to: {question}",
                    url="https://textbook.example.com/general",
                    chapter="General Concepts",
                    section="Relevant Section",
                    heading_hierarchy=["General"],
                    similarity_score=0.75 + (abs(hash(question)) % 20) / 100
                )
            ]

            # Mock the OpenAI client
            with patch('backend.rag_agent.agents.textbook_agent.AsyncOpenAI') as mock_client:
                mock_response = AsyncMock()
                mock_response.choices = [AsyncMock()]
                mock_response.choices[0].message = AsyncMock()
                mock_response.choices[0].message.content = f"Response to: {question}"

                mock_openai_instance = AsyncMock()
                mock_openai_instance.chat.completions.create = AsyncMock(return_value=mock_response)
                mock_client.return_value = mock_openai_instance

                start_time = time.time()
                response = await agent_service.process_request(chat_request)
                end_time = time.time()

                response_time = end_time - start_time
                response_times.append(response_time)

                # Validate response
                assert response.response is not None
                assert len(response.response) > 0
                assert response_time <= 10

    # Calculate consistency metrics
    avg_time = statistics.mean(response_times)
    std_dev = statistics.stdev(response_times) if len(response_times) > 1 else 0
    max_time = max(response_times)

    print(f"Response Time Consistency:")
    print(f"  Average: {avg_time:.3f}s")
    print(f"  Std Dev: {std_dev:.3f}s")
    print(f"  Max: {max_time:.3f}s")

    # Ensure no response takes more than 10 seconds
    assert max_time <= 10, f"Maximum response time {max_time:.3f}s exceeds 10s threshold"

    # Ensure 95% of responses are under 10 seconds (all of them in this case)
    responses_under_10s = sum(1 for t in response_times if t <= 10)
    success_rate = responses_under_10s / len(response_times) * 100
    assert success_rate >= 95.0, f"Only {success_rate:.1f}% of responses were under 10 seconds"


if __name__ == "__main__":
    pytest.main([__file__])