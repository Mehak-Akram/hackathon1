"""
RAG Retrieval Pipeline for Physical AI Textbook

This module implements semantic search functionality against Qdrant Cloud
using Cohere-generated embeddings to support downstream AI agents.
"""
import os
import logging
import time
from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel, Field
import cohere
from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Query(BaseModel):
    """Query model for natural language input with validation"""
    text: str = Field(..., description="The natural language query from user/agent")
    top_k: int = Field(default=5, description="Number of results to retrieve, default 5")


class RetrievedChunk(BaseModel):
    """Model for retrieved content chunks with complete metadata"""
    content: str = Field(..., description="The actual text content of the chunk")
    chunk_id: str = Field(..., description="Unique identifier for the chunk in Qdrant")
    url: str = Field(..., description="Source URL of the content")
    chapter: str = Field(..., description="Chapter name/identifier from hierarchy")
    section: str = Field(..., description="Section name within chapter")
    heading_hierarchy: List[str] = Field(..., description="Hierarchy of headings from the document")
    similarity_score: float = Field(..., description="Cosine similarity score between query and chunk")
    metadata: Optional[Dict] = Field(default=None, description="Additional metadata as key-value pairs")


class ValidationQuery(BaseModel):
    """Model for validation queries with expected results"""
    query_text: str = Field(..., description="The input query text")
    expected_chunks: List[str] = Field(..., description="Expected chunk IDs or content for validation")
    query_category: str = Field(..., description="Category of query for testing")


class ValidationResult(BaseModel):
    """Model for validation results with accuracy metrics"""
    query_id: str = Field(..., description="Identifier for the test query")
    retrieved_chunks: List[RetrievedChunk] = Field(..., description="Chunks returned by the system")
    expected_chunks: List[str] = Field(..., description="Chunks that should have been returned")
    accuracy_score: float = Field(..., description="Measured accuracy for this query")
    precision: float = Field(..., description="Precision metric")
    recall: float = Field(..., description="Recall metric")
    is_correct: bool = Field(..., description="Whether retrieval was considered correct")
    execution_time: float = Field(..., description="Time taken for retrieval in seconds")


class QdrantSearchResult(BaseModel):
    """Model for Qdrant search results"""
    points: List[RetrievedChunk] = Field(..., description="Retrieved points from Qdrant")
    search_params: Dict = Field(..., description="Parameters used for the search")
    total_points_found: int = Field(..., description="Total number of points found before top-k filtering")
    execution_time: float = Field(..., description="Time taken for the search operation")


def get_embedding(text: str) -> List[float]:
    """
    Generate embedding vector for input text using Cohere
    """
    logger.info(f"Generating embedding for text: {text[:50]}...")

    # Initialize Cohere client
    cohere_api_key = os.getenv("COHERE_API_KEY")
    if not cohere_api_key:
        raise ValueError("COHERE_API_KEY environment variable not set")

    co = cohere.Client(cohere_api_key)

    try:
        # Generate embedding using the same model as Spec-1 (multilingual-v3.0)
        response = co.embed(
            texts=[text],
            model="embed-multilingual-v3.0",  # Using multilingual model for broader compatibility
            input_type="search_query"  # Using search_query for query embeddings
        )

        embedding = response.embeddings[0]
        logger.info(f"Generated embedding with {len(embedding)} dimensions")

        return embedding

    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        raise


def validate_embedding_dimensions(vector: List[float]) -> bool:
    """
    Validate that embedding vector has correct dimensions (1024 for Cohere multilingual-v3.0)
    """
    expected_dim = 1024
    actual_dim = len(vector)

    if actual_dim == expected_dim:
        logger.debug(f"Embedding dimension validation passed: {actual_dim} dimensions")
        return True
    else:
        logger.error(f"Embedding dimension validation failed: expected {expected_dim}, got {actual_dim}")
        return False


def initialize_qdrant_client():
    """
    Create Qdrant client with proper configuration
    """
    logger.info("Initializing Qdrant client")

    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")

    if not qdrant_url or not qdrant_api_key:
        raise ValueError("QDRANT_URL and QDRANT_API_KEY environment variables must be set")

    client = QdrantClient(
        url=qdrant_url,
        api_key=qdrant_api_key,
        prefer_grpc=False  # Using HTTP for simplicity
    )

    logger.info(f"Qdrant client initialized for collection: ragchtbot_embadding")
    return client


def format_for_agent(chunks: List[RetrievedChunk]) -> List[Dict]:
    """
    Format retrieved chunks for agent-ready consumption
    """
    logger.debug(f"Formatting {len(chunks)} chunks for agent consumption")

    formatted_chunks = []
    for chunk in chunks:
        formatted_chunk = {
            "content": chunk.content,
            "source": {
                "url": chunk.url,
                "chapter": chunk.chapter,
                "section": chunk.section,
                "heading_hierarchy": chunk.heading_hierarchy
            },
            "similarity_score": chunk.similarity_score,
            "chunk_id": chunk.chunk_id
        }
        formatted_chunks.append(formatted_chunk)

    logger.debug(f"Formatted {len(formatted_chunks)} chunks for agent consumption")
    return formatted_chunks


def search_qdrant(query_embedding: List[float], top_k: int = 5) -> List[RetrievedChunk]:
    """
    Perform vector similarity search in Qdrant
    """
    logger.info(f"Performing Qdrant search with top_k={top_k}")

    # Validate embedding dimensions
    if not validate_embedding_dimensions(query_embedding):
        raise ValueError("Invalid embedding dimensions")

    # Initialize Qdrant client
    client = initialize_qdrant_client()
    collection_name = os.getenv("QDRANT_COLLECTION_NAME", "ragchtbot_embadding")

    start_time = time.time()

    try:
        # Perform the search - using the correct method name for Qdrant client
        from qdrant_client.http import models
        search_response = client.query_points(
            collection_name=collection_name,
            query=query_embedding,
            limit=top_k,
            with_payload=True  # Include payload with metadata
        )

        # The query_points method returns a QueryResponse object with a 'points' attribute
        # that contains a list of ScoredPoint objects
        retrieved_chunks = []
        for point in search_response.points:  # Access the points attribute
            payload = point.payload
            point_id = point.id
            score = point.score

            chunk = RetrievedChunk(
                content=payload.get("content", ""),
                chunk_id=point_id,
                url=payload.get("url", ""),
                chapter=payload.get("chapter", ""),
                section=payload.get("section", ""),
                heading_hierarchy=payload.get("heading_hierarchy", []),
                similarity_score=score,
                metadata=payload
            )
            retrieved_chunks.append(chunk)

        execution_time = time.time() - start_time
        logger.info(f"Qdrant search completed in {execution_time:.3f}s, found {len(retrieved_chunks)} results")

        return retrieved_chunks

    except AttributeError as e:
        # If query_points method doesn't exist, try the older search method
        logger.warning(f"Query points method not available, trying older search method: {str(e)}")

        try:
            # Use the older search method as fallback
            search_results = client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=top_k,
                with_payload=True
            )

            # Convert results to RetrievedChunk objects
            # The older search method returns a list of models.ScoredPoint objects directly
            retrieved_chunks = []
            for point in search_results:
                payload = point.payload
                point_id = point.id
                score = point.score

                chunk = RetrievedChunk(
                    content=payload.get("content", ""),
                    chunk_id=point_id,
                    url=payload.get("url", ""),
                    chapter=payload.get("chapter", ""),
                    section=payload.get("section", ""),
                    heading_hierarchy=payload.get("heading_hierarchy", []),
                    similarity_score=score,
                    metadata=payload
                )
                retrieved_chunks.append(chunk)

            execution_time = time.time() - start_time
            logger.info(f"Qdrant search completed in {execution_time:.3f}s, found {len(retrieved_chunks)} results")

            return retrieved_chunks

        except Exception as e2:
            logger.error(f"Error during Qdrant search: {str(e2)}")
            raise
    except Exception as e:
        logger.error(f"Error during Qdrant search: {str(e)}")
        raise


def retrieve_content(query: str, top_k: int = 5) -> List[RetrievedChunk]:
    """
    Perform semantic search and retrieve top-k relevant content chunks
    """
    logger.info(f"Starting retrieval for query: {query}")

    start_time = time.time()

    try:
        # Generate embedding for the query
        query_embedding = get_embedding(query)

        # Perform the search
        results = search_qdrant(query_embedding, top_k)

        execution_time = time.time() - start_time
        logger.info(f"Retrieval completed in {execution_time:.3f}s")

        # Log performance if it exceeds threshold
        if execution_time > 1.0:
            logger.warning(f"Retrieval exceeded 1-second threshold: {execution_time:.3f}s")

        return results

    except Exception as e:
        logger.error(f"Error during content retrieval: {str(e)}")
        raise


def validate_retrieval(queries: List[ValidationQuery]) -> List[ValidationResult]:
    """
    Validate retrieval quality against known queries
    """
    logger.info(f"Starting validation for {len(queries)} queries")

    results = []

    for i, validation_query in enumerate(queries):
        logger.info(f"Validating query {i+1}/{len(queries)}: {validation_query.query_text}")

        start_time = time.time()

        try:
            # Retrieve content for the query
            retrieved_chunks = retrieve_content(validation_query.query_text, top_k=5)

            # Extract chunk IDs from retrieved results
            retrieved_chunk_ids = [chunk.chunk_id for chunk in retrieved_chunks]

            # Calculate accuracy metrics
            expected_set = set(validation_query.expected_chunks)
            retrieved_set = set(retrieved_chunk_ids)

            # Calculate precision and recall
            if len(retrieved_set) > 0:
                precision = len(expected_set.intersection(retrieved_set)) / len(retrieved_set)
            else:
                precision = 0.0

            if len(expected_set) > 0:
                recall = len(expected_set.intersection(retrieved_set)) / len(expected_set)
            else:
                recall = 1.0  # If no expected chunks, we can't miss any

            # Calculate F1 score as accuracy metric
            if precision + recall > 0:
                accuracy_score = 2 * (precision * recall) / (precision + recall)
            else:
                accuracy_score = 0.0

            # Determine if correct (using a threshold)
            is_correct = accuracy_score >= 0.5  # Using 50% as threshold for "correct"

            execution_time = time.time() - start_time

            # Create validation result
            result = ValidationResult(
                query_id=f"validation_query_{i+1}",
                retrieved_chunks=retrieved_chunks,
                expected_chunks=validation_query.expected_chunks,
                accuracy_score=accuracy_score,
                precision=precision,
                recall=recall,
                is_correct=is_correct,
                execution_time=execution_time
            )

            results.append(result)

            logger.info(f"Query {i+1} validation: accuracy={accuracy_score:.3f}, precision={precision:.3f}, recall={recall:.3f}, correct={is_correct}")

        except Exception as e:
            logger.error(f"Error validating query {i+1}: {str(e)}")
            # Create a failed validation result
            result = ValidationResult(
                query_id=f"validation_query_{i+1}",
                retrieved_chunks=[],
                expected_chunks=validation_query.expected_chunks,
                accuracy_score=0.0,
                precision=0.0,
                recall=0.0,
                is_correct=False,
                execution_time=time.time() - start_time
            )
            results.append(result)

    logger.info(f"Validation completed for {len(queries)} queries")
    return results


def main():
    """
    Main function to demonstrate the retrieval pipeline
    """
    logger.info("RAG Retrieval Pipeline started")

    # Example usage
    try:
        # Example query
        query = "What are the fundamental principles of physical AI?"
        results = retrieve_content(query, top_k=3)

        print(f"\nQuery: {query}")
        print(f"Found {len(results)} relevant chunks:\n")

        for i, chunk in enumerate(results, 1):
            print(f"{i}. Score: {chunk.similarity_score:.3f}")
            print(f"   Chapter: {chunk.chapter}")
            print(f"   Section: {chunk.section}")
            print(f"   URL: {chunk.url}")
            print(f"   Content Preview: {chunk.content[:200]}...")
            print()

        # Format for agent consumption
        agent_ready_chunks = format_for_agent(results)
        print(f"Formatted {len(agent_ready_chunks)} chunks for agent consumption")

    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()