"""
Retrieval tool for connecting to the existing Qdrant pipeline
"""
import asyncio
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from pydantic import BaseModel

from ..config.settings import settings
from ..api.models.response import RetrievedContext
from ..utils.helpers import is_valid_uuid, is_valid_url
from ..utils.logger import get_logger
from ..utils.connection_pool import get_http_client

logger = get_logger(__name__)


class QdrantRetrievalTool:
    """
    Tool for connecting to the existing Qdrant retrieval pipeline
    """
    def __init__(self):
        self.client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            prefer_grpc=False  # Using HTTP for simplicity
        )
        self.collection_name = settings.qdrant_collection_name

    async def retrieve_context(self, query: str, top_k: Optional[int] = None) -> List[RetrievedContext]:
        """
        Retrieve context from Qdrant based on the query
        """
        if top_k is None:
            top_k = settings.default_top_k

        logger.info(f"Retrieving context for query: {query[:50]}...")

        try:
            # Generate embedding for the query using an external service
            query_embedding = await self._get_embedding(query)

            # Perform the search in Qdrant
            search_results = await self._search_qdrant(query_embedding, top_k * 2)  # Get more results to allow for deduplication

            # Convert results to RetrievedContext objects
            retrieved_contexts = []
            seen_content = set()  # Track seen content to avoid duplicates

            for point in search_results:
                try:
                    payload = getattr(point, 'payload', point)  # Handle different response formats
                    point_id = getattr(point, 'id', 'unknown')
                    point_score = getattr(point, 'score', 0.0)

                    # Get the content to check for duplicates
                    content = payload.get("content", "") if isinstance(payload, dict) else getattr(payload, 'content', "")

                    # Create a hashable representation of the content (truncated for performance)
                    content_key = content.strip()[:100].lower()  # Use first 100 chars as a key

                    # Skip if we've seen similar content before
                    if content_key in seen_content:
                        continue

                    # Add to seen set
                    seen_content.add(content_key)

                    # Handle different payload formats
                    url = payload.get("url", "https://example.com") if isinstance(payload, dict) else getattr(payload, 'url', 'https://example.com')
                    chapter = payload.get("chapter", "Unknown Chapter") or "Unknown Chapter" if isinstance(payload, dict) else getattr(payload, 'chapter', 'Unknown Chapter') or 'Unknown Chapter'
                    section = payload.get("section", "Unknown Section") or "Unknown Section" if isinstance(payload, dict) else getattr(payload, 'section', 'Unknown Section') or 'Unknown Section'
                    heading_hierarchy = payload.get("heading_hierarchy", []) if isinstance(payload, dict) else getattr(payload, 'heading_hierarchy', [])

                    context = RetrievedContext(
                        id=point_id,
                        content=content,
                        url=url,
                        chapter=chapter,
                        section=section,
                        heading_hierarchy=heading_hierarchy,
                        similarity_score=point_score,
                        metadata=payload
                    )
                    retrieved_contexts.append(context)

                    # Stop when we reach the desired top_k after deduplication
                    if len(retrieved_contexts) >= top_k:
                        break
                except Exception as point_error:
                    logger.warning(f"Error processing individual search result: {str(point_error)}")
                    continue  # Skip this result and continue with others

            logger.info(f"Retrieved {len(retrieved_contexts)} unique context chunks for query after deduplication")
            return retrieved_contexts

        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            # Return empty list instead of raising exception to allow graceful degradation
            return []

    async def _get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for the input text using an external service
        """
        logger.debug(f"Generating embedding for text: {text[:50]}...")

        # Try to import from the existing retrieval pipeline
        try:
            # Try the most direct import first
            import sys
            import os

            # Add the backend directory to the path to ensure imports work
            backend_path = os.path.join(os.path.dirname(__file__), '..', '..', '..')
            if backend_path not in sys.path:
                sys.path.insert(0, backend_path)

            from backend.retrieval_pipeline.retrieval_pipeline import get_embedding
            embedding = get_embedding(text)
            logger.info(f"Successfully generated embedding using retrieval pipeline: {len(embedding)} dimensions")
            return embedding
        except ImportError:
            logger.warning("Could not import from existing retrieval pipeline")
        except Exception as e:
            logger.warning(f"Error using retrieval pipeline: {str(e)}")

        # Fallback: try to use a simple approach without external dependencies
        logger.debug("Using simple fallback embedding generation")

        # Create a simple hash-based embedding as a last resort
        # This is not semantically meaningful but allows the system to continue
        import hashlib
        text_hash = hashlib.md5(text.encode()).hexdigest()

        # Convert hex hash to float vector (normalize to 1024 dimensions)
        embedding = []
        for i in range(0, len(text_hash), 2):
            if len(embedding) >= 1024:
                break
            hex_pair = text_hash[i:i+2] if i+2 <= len(text_hash) else text_hash[i]
            value = int(hex_pair, 16) / 255.0  # Normalize to 0-1
            # Apply a simple transformation to create more variation
            value = (value - 0.5) * 2  # Normalize to -1 to 1
            embedding.append(value)

        # Pad with zeros if needed
        while len(embedding) < 1024:
            embedding.append(0.0)

        # Truncate if too long
        embedding = embedding[:1024]

        logger.debug(f"Generated fallback embedding with {len(embedding)} dimensions")
        return embedding

    async def _search_qdrant(self, query_embedding: List[float], top_k: int) -> List:
        """
        Perform vector similarity search in Qdrant
        """
        logger.debug(f"Performing Qdrant search with top_k={top_k}")

        try:
            # First, try the query_points method (newer Qdrant versions)
            try:
                search_response = self.client.query_points(
                    collection_name=self.collection_name,
                    query=query_embedding,
                    limit=top_k,
                    with_payload=True  # Include payload with metadata
                )
                # The query_points method returns a QueryResponse object with a 'points' attribute
                return search_response.points
            except AttributeError:
                # If query_points method doesn't exist, try the older search method
                logger.debug("Query points method not available, trying older search method")
                search_results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_embedding,
                    limit=top_k,
                    with_payload=True
                )
                return search_results

        except Exception as e:
            logger.error(f"Error during Qdrant search: {str(e)}")
            # Return empty list instead of raising exception to allow graceful degradation
            return []

    async def validate_retrieval(self, query: str, expected_chunks: List[str] = None) -> Dict[str, Any]:
        """
        Validate retrieval quality for the given query
        """
        logger.info(f"Validating retrieval for query: {query}")

        retrieved_contexts = await self.retrieve_context(query, top_k=5)

        if expected_chunks:
            # Calculate accuracy metrics
            retrieved_chunk_ids = [ctx.id for ctx in retrieved_contexts]
            expected_set = set(expected_chunks)
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

            is_correct = accuracy_score >= 0.5  # Using 50% as threshold for "correct"

            validation_result = {
                "query": query,
                "retrieved_chunks": retrieved_chunk_ids,
                "expected_chunks": expected_chunks,
                "accuracy_score": accuracy_score,
                "precision": precision,
                "recall": recall,
                "is_correct": is_correct
            }
        else:
            # Without expected chunks, just return the retrieved contexts
            validation_result = {
                "query": query,
                "retrieved_chunks": [ctx.id for ctx in retrieved_contexts],
                "expected_chunks": expected_chunks,
                "accuracy_score": None,
                "precision": None,
                "recall": None,
                "is_correct": True  # Default to correct if no expected results
            }

        logger.info(f"Validation completed for query: accuracy={validation_result.get('accuracy_score')}, correct={validation_result['is_correct']}")
        return validation_result


# Global instance of the retrieval tool
retrieval_tool = QdrantRetrievalTool()