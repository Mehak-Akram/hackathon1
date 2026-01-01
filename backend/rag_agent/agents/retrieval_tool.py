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
        Retrieve context from Qdrant based on the query with enhanced logic
        """
        if top_k is None:
            top_k = settings.default_top_k

        logger.info(f"Retrieving context for query: {query[:50]}...")

        try:
            # Generate embedding for the query using an external service
            query_embedding = await self._get_embedding(query)

            # Perform the search in Qdrant with more results to allow for better selection
            search_results = await self._search_qdrant(query_embedding, top_k * 3)  # Get more results for better selection

            # Convert results to RetrievedContext objects
            retrieved_contexts = []
            seen_content = set()  # Track seen content to avoid duplicates
            seen_urls = set()     # Track URLs to avoid duplicate sources

            for point in search_results:
                try:
                    payload = getattr(point, 'payload', point)  # Handle different response formats
                    point_id = getattr(point, 'id', 'unknown')
                    point_score = getattr(point, 'score', 0.0)

                    # Get the content to check for duplicates
                    content = payload.get("content", "") if isinstance(payload, dict) else getattr(payload, 'content', "")

                    if not content.strip():
                        continue  # Skip empty content

                    # Create a hashable representation of the content (truncated for performance)
                    content_key = content.strip()[:100].lower()  # Use first 100 chars as a key
                    url = payload.get("url", "") if isinstance(payload, dict) else getattr(payload, 'url', '')

                    # Skip if we've seen similar content before or same URL
                    if content_key in seen_content or url in seen_urls:
                        continue

                    # Add to seen sets
                    seen_content.add(content_key)
                    if url:
                        seen_urls.add(url)

                    # Handle different payload formats
                    url = payload.get("url", "https://example.com") if isinstance(payload, dict) else getattr(payload, 'url', 'https://example.com')
                    chapter = payload.get("chapter", "Unknown Chapter") or "Unknown Chapter" if isinstance(payload, dict) else getattr(payload, 'chapter', 'Unknown Chapter') or 'Unknown Chapter'
                    section = payload.get("section", "Unknown Section") or "Unknown Section" if isinstance(payload, dict) else getattr(payload, 'section', 'Unknown Section') or 'Unknown Section'
                    heading_hierarchy = payload.get("heading_hierarchy", []) if isinstance(payload, dict) else getattr(payload, 'heading_hierarchy', [])

                    # Calculate a quality-adjusted score
                    quality_score = self._calculate_quality_score(content, point_score)

                    context = RetrievedContext(
                        id=point_id,
                        content=content,
                        url=url,
                        chapter=chapter,
                        section=section,
                        heading_hierarchy=heading_hierarchy,
                        similarity_score=quality_score,  # Use quality-adjusted score
                        metadata=payload
                    )
                    retrieved_contexts.append(context)

                    # Stop when we reach the desired top_k after deduplication
                    if len(retrieved_contexts) >= top_k:
                        break
                except Exception as point_error:
                    logger.warning(f"Error processing individual search result: {str(point_error)}")
                    continue  # Skip this result and continue with others

            # Sort by similarity score in descending order after deduplication
            retrieved_contexts.sort(key=lambda x: x.similarity_score, reverse=True)

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
            backend_path = os.path.join(os.path.dirname(__file__), '..', '..')
            if backend_path not in sys.path:
                sys.path.insert(0, backend_path)

            from retrieval_pipeline.retrieval_pipeline import get_embedding
            embedding = get_embedding(text)
            logger.info(f"Successfully generated embedding using retrieval pipeline: {len(embedding)} dimensions")
            return embedding
        except ImportError:
            logger.error("Could not import from existing retrieval pipeline. This is a critical error.")
            raise
        except Exception as e:
            logger.error(f"Critical error using retrieval pipeline: {str(e)}")
            raise

    def _calculate_quality_score(self, content: str, base_similarity_score: float) -> float:
        """
        Calculate a quality-adjusted score considering content quality and relevance
        """
        # Start with the base similarity score
        quality_score = base_similarity_score

        # Adjust based on content quality factors

        # Length factor: very short content might be low quality
        if len(content.strip()) < 50:
            quality_score *= 0.7  # Reduce score for very short content

        # Check for repetitive content (common issue with "Complete Learning Path")
        repetitive_patterns = [
            'Complete Learning Path',
            'comprehensive journey',
            'ROS 2 fundamentals',
            'advanced humanoid robotics'
        ]

        for pattern in repetitive_patterns:
            if content.lower().count(pattern.lower()) > 1:
                quality_score *= 0.5  # Reduce score for repetitive content
                break

        # Check for keyword density - if content has relevant keywords, boost score
        technical_keywords = [
            'vision-language-action', 'humanoid control', 'robotics', 'ai', 'physical ai',
            'vla models', 'embodied ai', 'robot control', 'machine learning', 'deep learning',
            'neural networks', 'computer vision', 'natural language', 'action planning',
            'physical ai', 'humanoid robotics', 'action models', 'language models'
        ]

        content_lower = content.lower()
        keyword_matches = sum(1 for keyword in technical_keywords if keyword in content_lower)

        if keyword_matches > 0:
            # Boost score for content with relevant keywords
            quality_score = min(1.0, quality_score * (1.0 + keyword_matches * 0.2))  # Increased boost

        # Check for technical term density - more technical terms = higher quality for technical queries
        technical_terms = [
            'algorithm', 'function', 'method', 'process', 'system', 'model', 'framework',
            'architecture', 'protocol', 'procedure', 'technique', 'approach', 'theory',
            'principle', 'concept', 'definition', 'equation', 'formula', 'implementation'
        ]

        technical_term_matches = sum(1 for term in technical_terms if term in content_lower)
        if technical_term_matches > 0:
            quality_score = min(1.0, quality_score * (1.0 + technical_term_matches * 0.1))  # Increased boost

        # Ensure minimum quality for relevant content even with low similarity
        if keyword_matches > 0 and quality_score < 0.3:
            quality_score = max(quality_score, 0.3)  # Ensure minimum quality for relevant content

        # Ensure score stays within 0-1 range
        quality_score = max(0.0, min(1.0, quality_score))

        return quality_score

    def _expand_query(self, query: str) -> str:
        """
        Expand the query with related terms to improve retrieval
        """
        query_lower = query.lower()

        # Define expansion terms for key concepts
        expansion_terms = {
            'physical ai': ['embodied ai', 'robotics', 'real-world ai', 'robot intelligence', 'physical artificial intelligence'],
            'humanoid robotics': ['humanoid robot', 'bipedal robot', 'human-like robot', 'walking robot', 'humanoid robot control'],
            'vision-language-action': ['vla', 'multimodal models', 'vision language action models', 'vlm', 'multimodal ai'],
            'humanoid control': ['locomotion', 'balance control', 'gait control', 'bipedal control', 'humanoid locomotion', 'walking control'],
            'robotics': ['robot', 'automation', 'control systems', 'mechatronics', 'robot control'],
            'ai': ['artificial intelligence', 'machine learning', 'neural networks', 'deep learning'],
            'vla models': ['vision language action models', 'multimodal models', 'vision-language-action', 'vlm'],
            'embodied ai': ['embodied artificial intelligence', 'physical ai', 'robotics', 'embodied intelligence'],
        }

        expanded_query = query

        # Add expansion terms if relevant concepts are found
        for concept, expansions in expansion_terms.items():
            if concept in query_lower:
                expanded_query += " " + " ".join(expansions)

        # Additional expansion: if query contains technical terms, add synonyms
        technical_expansions = {
            'control': ['control system', 'controller', 'control theory', 'feedback control'],
            'learning': ['machine learning', 'deep learning', 'reinforcement learning', 'supervised learning'],
            'model': ['models', 'neural network', 'algorithm', 'architecture'],
            'vision': ['computer vision', 'visual perception', 'image processing'],
            'language': ['natural language processing', 'nlp', 'text processing'],
            'action': ['action planning', 'motion planning', 'robot action', 'manipulation'],
        }

        for term, expansions in technical_expansions.items():
            if term in query_lower:
                expanded_query += " " + " ".join(expansions)

        return expanded_query

    async def retrieve_context_with_expansion(self, query: str, top_k: Optional[int] = None) -> List:
        """
        Retrieve context with query expansion for better matching
        """
        if top_k is None:
            top_k = settings.default_top_k

        logger.info(f"Retrieving context for query: {query[:50]}...")

        try:
            # First, try with original query
            original_query_embedding = await self._get_embedding(query)
            original_results = await self._search_qdrant(original_query_embedding, top_k * 2)  # Get more results

            # If low similarity scores, try with expanded query
            avg_similarity = sum(getattr(point, 'score', 0) for point in original_results) / max(len(original_results), 1)

            # Lower the threshold to trigger expansion for technical queries
            # Also consider technical keywords in the query to trigger expansion
            query_lower = query.lower()
            has_technical_terms = any(term in query_lower for term in [
                'vision-language-action', 'humanoid control', 'vla', 'robotics',
                'physical ai', 'embodied ai', 'machine learning', 'deep learning',
                'neural networks', 'computer vision', 'nlp'
            ])

            if avg_similarity < 0.5 or has_technical_terms:  # Lower threshold and trigger for technical terms
                expanded_query = self._expand_query(query)
                logger.info(f"Low similarity detected ({avg_similarity:.3f}), expanding query to: {expanded_query[:100]}...")

                try:
                    expanded_query_embedding = await self._get_embedding(expanded_query)
                    expanded_results = await self._search_qdrant(expanded_query_embedding, top_k * 2)

                    # Combine and deduplicate results
                    all_results = original_results + expanded_results

                    # Convert results to RetrievedContext objects with deduplication
                    retrieved_contexts = []
                    seen_content = set()
                    seen_urls = set()

                    for point in all_results:
                        try:
                            payload = getattr(point, 'payload', point)  # Handle different response formats
                            point_id = getattr(point, 'id', 'unknown')
                            point_score = getattr(point, 'score', 0.0)

                            # Get the content to check for duplicates
                            content = payload.get("content", "") if isinstance(payload, dict) else getattr(payload, 'content', "")

                            if not content.strip():
                                continue  # Skip empty content

                            # Create a hashable representation of the content (truncated for performance)
                            content_key = content.strip()[:100].lower()  # Use first 100 chars as a key
                            url = payload.get("url", "") if isinstance(payload, dict) else getattr(payload, 'url', '')

                            # Skip if we've seen similar content before or same URL
                            if content_key in seen_content or url in seen_urls:
                                continue

                            # Add to seen sets
                            seen_content.add(content_key)
                            if url:
                                seen_urls.add(url)

                            # Handle different payload formats
                            url = payload.get("url", "https://example.com") if isinstance(payload, dict) else getattr(payload, 'url', 'https://example.com')
                            chapter = payload.get("chapter", "Unknown Chapter") or "Unknown Chapter" if isinstance(payload, dict) else getattr(payload, 'chapter', 'Unknown Chapter') or 'Unknown Chapter'
                            section = payload.get("section", "Unknown Section") or "Unknown Section" if isinstance(payload, dict) else getattr(payload, 'section', 'Unknown Section') or 'Unknown Section'
                            heading_hierarchy = payload.get("heading_hierarchy", []) if isinstance(payload, dict) else getattr(payload, 'heading_hierarchy', [])

                            # Calculate a quality-adjusted score
                            quality_score = self._calculate_quality_score(content, point_score)

                            context = RetrievedContext(
                                id=point_id,
                                content=content,
                                url=url,
                                chapter=chapter,
                                section=section,
                                heading_hierarchy=heading_hierarchy,
                                similarity_score=quality_score,  # Use quality-adjusted score
                                metadata=payload
                            )
                            retrieved_contexts.append(context)

                            # Stop when we reach the desired top_k after deduplication
                            if len(retrieved_contexts) >= top_k:
                                break
                        except Exception as point_error:
                            logger.warning(f"Error processing individual search result: {str(point_error)}")
                            continue  # Skip this result and continue with others

                    # Sort by similarity score in descending order after deduplication
                    retrieved_contexts.sort(key=lambda x: x.similarity_score, reverse=True)

                    logger.info(f"Retrieved {len(retrieved_contexts)} unique context chunks for expanded query after deduplication")
                    return retrieved_contexts
                except Exception as expand_error:
                    logger.warning(f"Query expansion failed: {str(expand_error)}, falling back to original results")

            # If we get here, use original results
            # Convert results to RetrievedContext objects with deduplication
            retrieved_contexts = []
            seen_content = set()
            seen_urls = set()

            for point in original_results:
                try:
                    payload = getattr(point, 'payload', point)  # Handle different response formats
                    point_id = getattr(point, 'id', 'unknown')
                    point_score = getattr(point, 'score', 0.0)

                    # Get the content to check for duplicates
                    content = payload.get("content", "") if isinstance(payload, dict) else getattr(payload, 'content', "")

                    if not content.strip():
                        continue  # Skip empty content

                    # Create a hashable representation of the content (truncated for performance)
                    content_key = content.strip()[:100].lower()  # Use first 100 chars as a key
                    url = payload.get("url", "") if isinstance(payload, dict) else getattr(payload, 'url', '')

                    # Skip if we've seen similar content before or same URL
                    if content_key in seen_content or url in seen_urls:
                        continue

                    # Add to seen sets
                    seen_content.add(content_key)
                    if url:
                        seen_urls.add(url)

                    # Handle different payload formats
                    url = payload.get("url", "https://example.com") if isinstance(payload, dict) else getattr(payload, 'url', 'https://example.com')
                    chapter = payload.get("chapter", "Unknown Chapter") or "Unknown Chapter" if isinstance(payload, dict) else getattr(payload, 'chapter', 'Unknown Chapter') or 'Unknown Chapter'
                    section = payload.get("section", "Unknown Section") or "Unknown Section" if isinstance(payload, dict) else getattr(payload, 'section', 'Unknown Section') or 'Unknown Section'
                    heading_hierarchy = payload.get("heading_hierarchy", []) if isinstance(payload, dict) else getattr(payload, 'heading_hierarchy', [])

                    # Calculate a quality-adjusted score
                    quality_score = self._calculate_quality_score(content, point_score)

                    context = RetrievedContext(
                        id=point_id,
                        content=content,
                        url=url,
                        chapter=chapter,
                        section=section,
                        heading_hierarchy=heading_hierarchy,
                        similarity_score=quality_score,  # Use quality-adjusted score
                        metadata=payload
                    )
                    retrieved_contexts.append(context)

                    # Stop when we reach the desired top_k after deduplication
                    if len(retrieved_contexts) >= top_k:
                        break
                except Exception as point_error:
                    logger.warning(f"Error processing individual search result: {str(point_error)}")
                    continue  # Skip this result and continue with others

            # Sort by similarity score in descending order after deduplication
            retrieved_contexts.sort(key=lambda x: x.similarity_score, reverse=True)

            logger.info(f"Retrieved {len(retrieved_contexts)} unique context chunks for original query after deduplication")
            return retrieved_contexts

        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            # Return empty list instead of raising exception to allow graceful degradation
            return []

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