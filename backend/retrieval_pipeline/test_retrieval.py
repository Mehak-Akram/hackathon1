"""
Testing script for RAG retrieval pipeline
This script tests the retrieval functionality with sample queries
"""
import os
from retrieval_pipeline import (
    retrieve_content,
    validate_retrieval,
    ValidationQuery,
    initialize_qdrant_client,
    get_embedding,
    validate_embedding_dimensions,
    format_for_agent
)
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_basic_retrieval():
    """Test basic retrieval functionality"""
    logger.info("Testing basic retrieval functionality")

    try:
        # Test with a sample query
        query = "What are neural networks?"
        results = retrieve_content(query, top_k=3)

        logger.info(f"Retrieved {len(results)} chunks for query: '{query}'")

        # Check that we got results
        assert len(results) > 0, "Should retrieve at least one chunk"

        # Check that each result has required fields
        for chunk in results:
            assert chunk.content, "Chunk should have content"
            assert chunk.chunk_id, "Chunk should have ID"
            assert chunk.url, "Chunk should have URL"
            assert chunk.chapter, "Chunk should have chapter"
            assert chunk.section, "Chunk should have section"
            assert chunk.similarity_score is not None, "Chunk should have similarity score"

        logger.info("✓ Basic retrieval test passed")
        return True

    except Exception as e:
        logger.error(f"✗ Basic retrieval test failed: {str(e)}")
        return False


def test_embedding_functionality():
    """Test embedding generation and validation"""
    logger.info("Testing embedding functionality")

    try:
        # Test embedding generation
        text = "This is a test sentence for embedding."
        embedding = get_embedding(text)

        # Check embedding dimensions
        is_valid = validate_embedding_dimensions(embedding)
        assert is_valid, "Embedding should have correct dimensions (1024)"

        # Check embedding length
        assert len(embedding) == 1024, f"Embedding should have 1024 dimensions, got {len(embedding)}"

        logger.info("✓ Embedding functionality test passed")
        return True

    except Exception as e:
        logger.error(f"✗ Embedding functionality test failed: {str(e)}")
        return False


def test_formatting_for_agent():
    """Test agent-ready formatting"""
    logger.info("Testing agent-ready formatting")

    try:
        # First get some results to format
        query = "What is machine learning?"
        results = retrieve_content(query, top_k=2)

        # Format for agent
        formatted = format_for_agent(results)

        # Check that formatting worked
        assert len(formatted) == len(results), "Should have same number of formatted chunks as original"

        # Check that each formatted chunk has expected structure
        for chunk in formatted:
            assert 'content' in chunk, "Formatted chunk should have content"
            assert 'source' in chunk, "Formatted chunk should have source"
            assert 'similarity_score' in chunk, "Formatted chunk should have similarity score"
            assert 'chunk_id' in chunk, "Formatted chunk should have chunk_id"

        logger.info("✓ Agent-ready formatting test passed")
        return True

    except Exception as e:
        logger.error(f"✗ Agent-ready formatting test failed: {str(e)}")
        return False


def test_semantic_matching():
    """Test that semantic matching works (not just keyword matching)"""
    logger.info("Testing semantic matching")

    try:
        # Test with a query that uses different terminology than the content might use
        query = "How do artificial neural systems learn?"
        results = retrieve_content(query, top_k=3)

        logger.info(f"Semantic matching test - retrieved {len(results)} chunks for query: '{query}'")

        # Check that we got results even though the query terminology might differ
        assert len(results) > 0, "Should retrieve chunks for semantically related query"

        # Check that similarity scores are reasonable (not all 0)
        scores = [chunk.similarity_score for chunk in results]
        assert any(score > 0.1 for score in scores), "Should have reasonable similarity scores"

        logger.info("✓ Semantic matching test passed")
        return True

    except Exception as e:
        logger.error(f"✗ Semantic matching test failed: {str(e)}")
        return False


def test_validation_framework():
    """Test the validation framework"""
    logger.info("Testing validation framework")

    try:
        # Create sample validation queries
        validation_queries = [
            ValidationQuery(
                query_text="What are neural networks?",
                expected_chunks=["test-chunk-1", "test-chunk-2"],  # These won't match actual results but will test the framework
                query_category="definition"
            ),
            ValidationQuery(
                query_text="How do machine learning algorithms work?",
                expected_chunks=["test-chunk-3"],
                query_category="concept"
            )
        ]

        # Run validation (this will likely show low accuracy since expected chunks don't match actual)
        results = validate_retrieval(validation_queries)

        logger.info(f"Validation framework test - processed {len(results)} queries")

        # Check that validation completed without errors
        assert len(results) == len(validation_queries), "Should have validation result for each query"

        # Check that each result has required fields
        for result in results:
            assert result.query_id, "Validation result should have query ID"
            assert result.accuracy_score is not None, "Validation result should have accuracy score"
            assert result.precision is not None, "Validation result should have precision"
            assert result.recall is not None, "Validation result should have recall"
            assert result.is_correct is not None, "Validation result should have correctness flag"
            assert result.execution_time is not None, "Validation result should have execution time"

        logger.info("✓ Validation framework test passed")
        return True

    except Exception as e:
        logger.error(f"✗ Validation framework test failed: {str(e)}")
        return False


def run_all_tests():
    """Run all tests and report results"""
    logger.info("Starting all retrieval pipeline tests")

    tests = [
        ("Embedding Functionality", test_embedding_functionality),
        ("Basic Retrieval", test_basic_retrieval),
        ("Agent Formatting", test_formatting_for_agent),
        ("Semantic Matching", test_semantic_matching),
        ("Validation Framework", test_validation_framework),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} ---")
        if test_func():
            passed += 1
        else:
            logger.error(f"{test_name} FAILED")

    logger.info(f"\n--- Test Results ---")
    logger.info(f"Passed: {passed}/{total}")
    logger.info(f"Success Rate: {passed/total*100:.1f}%")

    if passed == total:
        logger.info("🎉 All tests passed!")
        return True
    else:
        logger.warning("⚠ Some tests failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    if success:
        logger.info("Testing completed successfully!")
    else:
        logger.error("Testing completed with failures!")
        exit(1)