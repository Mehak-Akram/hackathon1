

"""
Validation script for RAG retrieval pipeline
This script validates retrieval quality against known textbook queries
"""
import os
from retrieval_pipeline import (
    retrieve_content,
    validate_retrieval,
    ValidationQuery,
    ValidationResult
)
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_comprehensive_validation():
    """
    Run comprehensive validation with 10+ representative textbook queries
    """
    logger.info("Starting comprehensive retrieval validation")

    # Define validation queries (these are example queries for textbook content)
    # In a real scenario, we would have specific expected chunk IDs
    validation_queries = [
        ValidationQuery(
            query_text="What are neural networks?",
            expected_chunks=["example-chunk-1"],  # Placeholder - would be actual chunk IDs in real validation
            query_category="definition"
        ),
        ValidationQuery(
            query_text="Explain machine learning algorithms",
            expected_chunks=["example-chunk-2"],
            query_category="concept"
        ),
        ValidationQuery(
            query_text="How do deep learning models work?",
            expected_chunks=["example-chunk-3"],
            query_category="concept"
        ),
        ValidationQuery(
            query_text="What is backpropagation?",
            expected_chunks=["example-chunk-4"],
            query_category="definition"
        ),
        ValidationQuery(
            query_text="Describe gradient descent optimization",
            expected_chunks=["example-chunk-5"],
            query_category="concept"
        ),
        ValidationQuery(
            query_text="What are convolutional neural networks?",
            expected_chunks=["example-chunk-6"],
            query_category="definition"
        ),
        ValidationQuery(
            query_text="Explain reinforcement learning",
            expected_chunks=["example-chunk-7"],
            query_category="concept"
        ),
        ValidationQuery(
            query_text="What is natural language processing?",
            expected_chunks=["example-chunk-8"],
            query_category="definition"
        ),
        ValidationQuery(
            query_text="How do transformers work?",
            expected_chunks=["example-chunk-9"],
            query_category="concept"
        ),
        ValidationQuery(
            query_text="What are generative adversarial networks?",
            expected_chunks=["example-chunk-10"],
            query_category="definition"
        ),
        ValidationQuery(
            query_text="Explain computer vision applications",
            expected_chunks=["example-chunk-11"],
            query_category="application"
        ),
        ValidationQuery(
            query_text="What is transfer learning?",
            expected_chunks=["example-chunk-12"],
            query_category="concept"
        )
    ]

    logger.info(f"Running validation on {len(validation_queries)} textbook queries")

    # Run validation
    results = validate_retrieval(validation_queries)

    # Calculate overall metrics
    total_queries = len(results)
    correct_queries = sum(1 for r in results if r.is_correct)
    avg_accuracy = sum(r.accuracy_score for r in results) / total_queries if total_queries > 0 else 0
    avg_precision = sum(r.precision for r in results) / total_queries if total_queries > 0 else 0
    avg_recall = sum(r.recall for r in results) / total_queries if total_queries > 0 else 0
    avg_execution_time = sum(r.execution_time for r in results) / total_queries if total_queries > 0 else 0

    logger.info("=== VALIDATION RESULTS ===")
    logger.info(f"Total Queries: {total_queries}")
    logger.info(f"Correct Retrievals: {correct_queries}")
    logger.info(f"Accuracy Rate: {correct_queries/total_queries*100:.1f}%")
    logger.info(f"Average Accuracy Score: {avg_accuracy:.3f}")
    logger.info(f"Average Precision: {avg_precision:.3f}")
    logger.info(f"Average Recall: {avg_recall:.3f}")
    logger.info(f"Average Execution Time: {avg_execution_time:.3f}s")

    # Check if we meet the success criteria
    accuracy_threshold_met = avg_accuracy >= 0.5  # Using 50% as threshold for demonstration
    performance_threshold_met = avg_execution_time < 1.0  # Sub-second performance

    logger.info(f"Accuracy threshold (50%) met: {accuracy_threshold_met}")
    logger.info(f"Performance threshold (1s) met: {performance_threshold_met}")

    # Detailed results
    logger.info("\n=== DETAILED RESULTS ===")
    for i, result in enumerate(results):
        logger.info(f"Query {i+1}: {validation_queries[i].query_text}")
        logger.info(f"  Accuracy: {result.accuracy_score:.3f}")
        logger.info(f"  Precision: {result.precision:.3f}")
        logger.info(f"  Recall: {result.recall:.3f}")
        logger.info(f"  Correct: {result.is_correct}")
        logger.info(f"  Time: {result.execution_time:.3f}s")
        logger.info(f"  Retrieved chunks: {len(result.retrieved_chunks)}")
        logger.info("  ---")

    # Summary
    success = accuracy_threshold_met and performance_threshold_met
    logger.info(f"\n=== OVERALL VALIDATION: {'PASSED' if success else 'FAILED'} ===")

    return success, results


def test_determinism():
    """
    Test that identical queries produce identical results (determinism)
    """
    logger.info("Testing pipeline determinism")

    query = "What are neural networks?"

    # Run the same query twice
    results1 = retrieve_content(query, top_k=3)
    results2 = retrieve_content(query, top_k=3)

    # Compare results
    same_content = [c.content for c in results1] == [c.content for c in results2]
    same_scores = [c.similarity_score for c in results1] == [c.similarity_score for c in results2]
    same_ids = [c.chunk_id for c in results1] == [c.chunk_id for c in results2]

    determinism_ok = same_content and same_scores and same_ids

    logger.info(f"Determinism test - Same content: {same_content}")
    logger.info(f"Determinism test - Same scores: {same_scores}")
    logger.info(f"Determinism test - Same IDs: {same_ids}")
    logger.info(f"Determinism: {'PASSED' if determinism_ok else 'FAILED'}")

    return determinism_ok


def test_performance():
    """
    Test retrieval performance under various conditions
    """
    logger.info("Testing retrieval performance")

    test_queries = [
        "What are neural networks?",
        "Explain machine learning",
        "How do deep learning models work?",
        "What is backpropagation?",
        "Describe gradient descent"
    ]

    execution_times = []
    for query in test_queries:
        import time
        start = time.time()
        try:
            results = retrieve_content(query, top_k=3)
            end = time.time()
            execution_time = end - start
            execution_times.append(execution_time)
            logger.info(f"Query: '{query[:30]}...', Time: {execution_time:.3f}s, Results: {len(results)}")
        except Exception as e:
            logger.error(f"Error with query '{query}': {str(e)}")

    if execution_times:
        avg_time = sum(execution_times) / len(execution_times)
        max_time = max(execution_times)
        p95_time = sorted(execution_times)[int(0.95 * len(execution_times))] if execution_times else 0

        logger.info(f"Performance Results:")
        logger.info(f"  Average time: {avg_time:.3f}s")
        logger.info(f"  Max time: {max_time:.3f}s")
        logger.info(f"  95th percentile time: {p95_time:.3f}s")
        logger.info(f"  Sub-second performance: {'PASSED' if max_time < 1.0 else 'FAILED'}")

        return max_time < 1.0  # Performance requirement
    else:
        logger.error("No successful queries to measure performance")
        return False


if __name__ == "__main__":
    logger.info("Starting RAG Retrieval Pipeline Validation")

    # Test determinism
    determinism_ok = test_determinism()

    # Test performance
    performance_ok = test_performance()

    # Run comprehensive validation
    validation_success, results = run_comprehensive_validation()

    # Overall assessment
    overall_success = determinism_ok and performance_ok and validation_success

    logger.info(f"\n=== FINAL VALIDATION ASSESSMENT: {'PASSED' if overall_success else 'FAILED'} ===")
    logger.info(f"Determinism: {'OK' if determinism_ok else 'FAIL'}")
    logger.info(f"Performance: {'OK' if performance_ok else 'FAIL'}")
    logger.info(f"Accuracy: {'OK' if validation_success else 'FAIL'}")

    if overall_success:
        logger.info("🎉 All validation criteria met!")
    else:
        logger.warning("⚠ Some validation criteria not met")
        exit(1)