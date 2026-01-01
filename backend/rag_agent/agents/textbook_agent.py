"""
Textbook agent implementation for the RAG Agent Service
"""
import asyncio
import time
from typing import List, Optional, Dict, Any
from openai import AsyncOpenAI
from pydantic import BaseModel

from ..config.settings import settings
from ..api.models.request import ChatRequest
from ..api.models.response import ChatResponse, Citation, AgentResponse, RetrievedContext
from ..utils.helpers import time_it_async, format_timestamp, log_error_with_context, safe_execute
from ..utils.logger import get_logger
from .retrieval_tool import retrieval_tool

logger = get_logger(__name__)


class TextbookAgent:
    """
    AI agent that answers questions about Physical AI concepts using textbook content
    """
    def __init__(self):
        # Use OpenRouter API as the primary LLM
        if settings.openrouter_api_key:
            # Configure OpenAI client to use OpenRouter
            self.client = AsyncOpenAI(
                api_key=settings.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1"
            )
            self.model = settings.agent_model  # Use configured model
            logger.info(f"Using OpenRouter API with model: {settings.agent_model}")
        elif settings.openai_api_key:
            # Fallback to OpenAI if no OpenRouter key provided
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
            self.model = settings.agent_model  # Use configured model
            logger.warning(f"Using OpenAI API as fallback with model: {settings.agent_model}")
        else:
            # If no key is provided, use a mock client that returns helpful error messages
            logger.warning("No API keys configured for LLM. Using mock client.")
            self.client = None
            self.model = "mock-model"
        self.retrieval_tool = retrieval_tool

    async def answer_question(
        self,
        question: str,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> ChatResponse:
        """
        Answer a question using retrieved textbook content
        Optimized for sub-10 second response time with caching and performance monitoring
        """
        start_time = time.time()
        logger.info(f"Processing question: {question[:50]}...")

        try:
            # Always use RAG for all questions (simplified approach without query classification)
            should_use_rag = True

            retrieved_contexts = []
            if should_use_rag:
                # Retrieve relevant context from the textbook with optimized parameters and query expansion
                retrieved_contexts = await self.retrieval_tool.retrieve_context_with_expansion(
                    query=question,
                    top_k=min(settings.default_top_k, 5)  # Limit to 5 for faster retrieval
                )
            else:
                # For greetings or casual chat, don't use RAG
                logger.info(f"Skipping RAG retrieval for greeting/casual query: {question[:50]}...")

            # Generate the answer using the retrieved context
            response_content = await self._generate_answer_with_context(
                question,
                retrieved_contexts,
                user_preferences,
                conversation_context=[]  # No conversation context for stateless operation
            )

            # Validate that the response is grounded in the retrieved content
            is_answer_valid = await self.validate_answer_grounding(
                question,
                response_content,
                retrieved_contexts
            )

            if not is_answer_valid:
                logger.warning(f"Generated answer may not be fully grounded in retrieved content for question: {question[:30]}...")
                # In a production system, you might want to handle this differently
                # For now, we'll continue with the response but log the issue

            # Extract citations from the retrieved contexts
            citations = self._extract_citations(retrieved_contexts)

            # Calculate response time ensuring it's always positive
            response_time = max(time.time() - start_time, 0.001)

            # Create the chat response
            chat_response = ChatResponse(
                response=response_content,
                citations=citations,
                retrieved_context_count=len(retrieved_contexts),
                response_time=response_time
            )

            logger.info(f"Generated response in {response_time:.3f}s with {len(citations)} citations")
            return chat_response

        except asyncio.TimeoutError:
            error_id = log_error_with_context(asyncio.TimeoutError(f"Timeout processing question: {question[:50]}..."), {
                "operation": "answer_question",
                "question": question[:50]
            })
            logger.error(f"Timeout processing question: {question[:50]}... - Error ID: {error_id}")
            # Return a helpful response instead of failing
            response_time = max(time.time() - start_time, 0.001)
            return ChatResponse(
                response="I'm sorry, but I'm taking too long to process your question. Please try rephrasing or ask a more specific question.",
                citations=[],
                retrieved_context_count=0,
                response_time=response_time
            )
        except Exception as e:
            error_id = log_error_with_context(e, {
                "operation": "answer_question",
                "question": question[:50]
            })
            logger.error(f"Error answering question '{question[:30]}...': {str(e)} - Error ID: {error_id}")
            # Return a graceful error response instead of raising exception
            # This allows the API route to return a proper response instead of an HTTP error
            response_time = max(time.time() - start_time, 0.001)
            return ChatResponse(
                response="I'm sorry, but I encountered an error while processing your question. Please try again.",
                citations=[],
                retrieved_context_count=0,
                response_time=response_time
            )

    async def _generate_answer_with_context(
        self,
        question: str,
        retrieved_contexts: List,
        user_preferences: Optional[Dict[str, Any]] = None,
        conversation_context: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Generate an answer using the retrieved context, conversation history, and OpenAI
        """
        # Filter out repetitive or low-quality contexts before formatting
        filtered_contexts = self._filter_repetitive_contexts(retrieved_contexts)

        # If no contexts after filtering or originally empty, still attempt to answer with general knowledge
        if not filtered_contexts:
            logger.info(f"No relevant contexts found for question: {question[:50]}...")
            # Instead of returning a failure message, build a prompt that allows the LLM to use general knowledge
            # but still acknowledge the context limitation
            prompt = f"You are an expert assistant for a Physical AI and Robotics textbook. " \
                     f"Answer the user's question to the best of your ability. " \
                     f"Note that no specific textbook content was retrieved for this query, " \
                     f"but please provide helpful information based on your general knowledge " \
                     f"of AI, robotics, and related fields.\n\n" \
                     f"USER QUESTION: {question}\n\n" \
                     f"ANSWER INSTRUCTIONS:\n" \
                     f"- Provide the best possible answer based on your knowledge\n" \
                     f"- If the topic is related to Physical AI, Robotics, Vision-Language-Action models, or Humanoid Control, " \
                     f"provide comprehensive explanations\n" \
                     f"- Be helpful and informative even without specific textbook context\n" \
                     f"- Mention if the information is from general knowledge rather than the textbook if relevant"

        # Only build the full prompt with context if we have contexts
        if filtered_contexts:
            # Format the retrieved contexts for the LLM
            formatted_context = self._format_context_for_llm(filtered_contexts)

            # For stateless operation, we don't use conversation history
            # Build the prompt with context
            detail_level = (user_preferences or {}).get('detail_level', 'intermediate')
            response_format = (user_preferences or {}).get('response_format', 'detailed')

            prompt = self._build_prompt(
                question=question,
                context=formatted_context,
                conversation_history="",  # No conversation history in stateless operation
                detail_level=detail_level,
                response_format=response_format
            )

        try:
            # Check if client is available (API keys are properly configured)
            if self.client is None:
                logger.warning("No LLM client configured. Returning helpful error message.")
                return ("I'm sorry, but I'm currently experiencing issues with the AI service due to missing or invalid API key configuration. "
                        "Please contact the system administrator to update the API key settings.")

            try:
                # Use OpenAI-compatible API to generate the response
                if self.client is not None and hasattr(self.client, 'chat') and hasattr(self.client.chat, 'completions'):
                    messages = [
                        {
                            "role": "system",
                            "content": (
                                "You are an expert assistant for a Physical AI and Robotics textbook. "
                                "When textbook context is provided, answer questions based on that context. "
                                "When no textbook context is provided, use your general knowledge of AI, robotics, and related fields "
                                "to provide helpful and accurate information. "
                                "Always provide source citations for information from the textbook context. "
                                "Consider the conversation history when answering follow-up questions. "
                                "IMPORTANT: Do not repeat or include repetitive phrases like 'Complete Learning Path' multiple times in your response. "
                                "For technical concepts like Vision-Language-Action models or Humanoid Control, provide comprehensive explanations."
                            )
                        }
                    ]

                    messages.append({
                        "role": "user",
                        "content": prompt
                    })

                    response = await self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        max_tokens=settings.max_response_tokens,
                        temperature=settings.temperature
                    )

                    # Handle OpenAI response structure
                    if not response or not hasattr(response, 'choices') or not response.choices:
                        logger.warning("Empty or invalid response from LLM")
                        answer = "I'm sorry, but I couldn't generate a response for your question."
                    else:
                        first_choice = response.choices[0]
                        if not hasattr(first_choice, 'message') or not hasattr(first_choice.message, 'content'):
                            logger.warning("Response choice missing message content")
                            answer = "I'm sorry, but I couldn't generate a response for your question."
                        else:
                            answer = first_choice.message.content
                else:
                    logger.warning("No LLM client configured or client type not supported")
                    answer = "I'm sorry, but I couldn't generate a response for your question."

                if answer:
                    answer = answer.strip()
                else:
                    answer = "I'm sorry, but I couldn't generate a response for your question."

                logger.debug(f"Generated answer: {answer[:100] if answer else 'None'}...")

                # Post-process the answer to remove any remaining repetitive content
                try:
                    cleaned_answer = self._remove_repetitive_content(answer)
                    logger.debug(f"Cleaned answer: {cleaned_answer[:100] if cleaned_answer else 'None'}...")
                except Exception as e:
                    logger.error(f"Error cleaning answer: {str(e)}")
                    cleaned_answer = answer  # Use original answer if cleaning fails

                return cleaned_answer
            except Exception as llm_error:
                logger.error(f"Error calling LLM API: {str(llm_error)}")

                # Check if it's an API key issue specifically
                if "leaked" in str(llm_error).lower() or "permission_denied" in str(llm_error).lower():
                    logger.error("API key issue detected - likely leaked key")
                    return ("I'm sorry, but I'm currently experiencing issues with the AI service due to an API key problem. "
                            "This may require updating the API key configuration. Please contact the system administrator.")
                elif "not found" in str(llm_error).lower() or "model" in str(llm_error).lower():
                    logger.error("Model not found issue detected")
                    return ("I'm sorry, but I'm having trouble connecting to the AI service. "
                            "The configured model might not be available. Please try again later.")
                else:
                    # Return a helpful response instead of failing completely
                    return "I'm sorry, but I'm having trouble connecting to the AI service right now. Please try again later."

        except Exception as e:
            error_id = log_error_with_context(e, {
                "operation": "llm_api_call",
                "question": question[:50],
                "model": settings.agent_model
            })
            logger.error(f"Error calling LLM API: {str(e)} - Error ID: {error_id}")
            raise

    def _format_conversation_history(self, conversation_history: List[Dict[str, str]]) -> str:
        """
        Format the conversation history for the LLM
        """
        formatted_history = []
        for i, turn in enumerate(conversation_history, 1):
            formatted_turn = f"Q{i}: {turn.get('question', '')}\nA{i}: {turn.get('response', '')}"
            formatted_history.append(formatted_turn)

        return "\n".join(formatted_history)

    def _format_context_for_llm(self, retrieved_contexts: List) -> str:
        """
        Format the retrieved contexts for the LLM with deduplication
        """
        formatted_contexts = []
        seen_content = set()

        for i, ctx in enumerate(retrieved_contexts, 1):
            # Create a hashable representation of the content to detect duplicates
            content_key = ctx.content.strip()[:100].lower()  # Use first 100 chars as a key

            # Skip if we've seen similar content before
            if content_key in seen_content:
                continue

            # Add to seen set
            seen_content.add(content_key)

            context_str = (
                f"Context {i}:\n"
                f"Chapter: {ctx.chapter}\n"
                f"Section: {ctx.section}\n"
                f"Content: {ctx.content}\n"
                f"URL: {ctx.url}\n"
                f"Similarity Score: {ctx.similarity_score}\n"
                "---\n"
            )
            formatted_contexts.append(context_str)

        return "\n".join(formatted_contexts)

    def _build_prompt(
        self,
        question: str,
        context: str,
        conversation_history: str = "",  # Not used in stateless operation
        detail_level: str = "intermediate",
        response_format: str = "detailed"
    ) -> str:
        """
        Build the prompt for the LLM based on user preferences
        """
        detail_instructions = {
            "basic": "Provide a simple, straightforward answer.",
            "intermediate": "Provide a moderately detailed answer with key points.",
            "advanced": "Provide a comprehensive, technical answer with details."
        }

        format_instructions = {
            "concise": "Keep the response brief and to the point.",
            "detailed": "Provide a thorough explanation with examples where appropriate.",
            "examples": "Include relevant examples from the context."
        }

        prompt = (
            f"You are an expert assistant for a Physical AI and Robotics textbook. "
            f"Answer the user's question based ONLY on the provided textbook content. "
            f"Do not hallucinate or provide information outside the provided context. "
            f"Always provide source citations for the information you provide.\n\n"

            f"TEXTBOOK CONTENT:\n{context}\n\n"
            f"USER QUESTION: {question}\n\n"

            f"ANSWER INSTRUCTIONS:\n"
            f"- Answer only based on the provided textbook content\n"
            f"- Do not provide information not found in the textbook\n"
            f"- Always cite the source of your information\n"
            f"- {detail_instructions.get(detail_level, detail_instructions['intermediate'])}\n"
            f"- {format_instructions.get(response_format, format_instructions['detailed'])}\n"
            f"- If the textbook content doesn't contain the answer, clearly state: 'I couldn't find specific information about this in the textbook content.'\n"
            f"- For technical concepts like Vision-Language-Action models or Humanoid Control, provide comprehensive explanations if available in the context\n"
            f"- Do not repeat or include repetitive phrases like 'Complete Learning Path' multiple times in your response\n"
        )

        return prompt

    def _extract_citations(self, retrieved_contexts: List) -> List[Citation]:
        """
        Extract citations from the retrieved contexts
        """
        citations = []
        for ctx in retrieved_contexts:
            citation = Citation(
                source_url=ctx.url,
                chapter=ctx.chapter,
                section=ctx.section,
                heading=ctx.heading_hierarchy[-1] if ctx.heading_hierarchy else None,
                page_reference=None,  # Page reference might not be available in all contexts
                similarity_score=ctx.similarity_score,
                text_excerpt=ctx.content[:200] + "..." if len(ctx.content) > 200 else ctx.content,  # First 200 chars as excerpt
                source_type="textbook",  # Default source type
                confidence_score=ctx.similarity_score  # Use similarity as confidence for now
            )
            citations.append(citation)

        return citations

    async def validate_answer_grounding(
        self,
        question: str,
        answer: str,
        retrieved_contexts: List
    ) -> bool:
        """
        Validate that the answer is grounded in the retrieved context
        """
        logger.info("Validating answer grounding...")

        # Check if the information in the answer is supported by the retrieved context
        context_text = " ".join([ctx.content for ctx in retrieved_contexts])
        context_text_lower = context_text.lower()

        # Remove repetitive content from the answer before validation
        # This helps prevent repetitive content from affecting the validation
        deduplicated_answer = self._remove_repetitive_content(answer)

        # This is a simple validation - in a real implementation,
        # you might want to use more sophisticated techniques
        answer_sentences = deduplicated_answer.split('. ')
        supported_sentences = 0

        for sentence in answer_sentences:
            sentence_clean = sentence.strip().lower()
            if len(sentence_clean) > 10:  # Only check meaningful sentences
                if sentence_clean in context_text_lower or \
                   any(word in context_text_lower for word in sentence_clean.split()[:5]):
                    supported_sentences += 1

        # If most sentences are supported by context, consider it grounded
        if len(answer_sentences) > 0:
            grounding_ratio = supported_sentences / len([s for s in answer_sentences if len(s.strip()) > 10])
            is_valid = grounding_ratio >= 0.6  # At least 60% of sentences should be grounded
        else:
            is_valid = False

        logger.info(f"Answer grounding validation: {supported_sentences}/{len([s for s in answer_sentences if len(s.strip()) > 10])} sentences supported ({is_valid})")
        return is_valid

    def _filter_repetitive_contexts(self, contexts: List) -> List:
        """
        Filter out repetitive contexts to prevent repetitive content in responses
        """
        if not contexts:
            return contexts

        # Filter out contexts that contain repetitive phrases
        filtered_contexts = []
        repetitive_patterns = [
            'Complete Learning Path',  # Common repetitive phrase from your issue
            'comprehensive journey',    # Related pattern
            'ROS 2 fundamentals',       # Related pattern
            'advanced humanoid robotics'  # Related pattern
        ]

        for ctx in contexts:
            try:
                # Check if ctx has content attribute
                if not hasattr(ctx, 'content'):
                    logger.warning(f"Context object missing 'content' attribute: {type(ctx)}")
                    filtered_contexts.append(ctx)  # Include it anyway to not break functionality
                    continue

                content = ctx.content or ""
                content_lower = content.lower()
                is_repetitive = False

                # Check if content contains repetitive patterns multiple times
                for pattern in repetitive_patterns:
                    if content_lower.count(pattern.lower()) > 1:
                        is_repetitive = True
                        break

                # Additional check: if the same phrase appears multiple times in the content
                if not is_repetitive:
                    # Check for other repetitive patterns
                    words = content_lower.split()
                    # Check if the content has too many repeated words (more than 30% of unique words)
                    if words:  # Only check if there are words
                        unique_words = set(words)
                        repetition_ratio = 1 - (len(unique_words) / len(words))
                        if repetition_ratio > 0.7:  # If more than 70% are repetitions (stricter check)
                            is_repetitive = True

                if not is_repetitive:
                    filtered_contexts.append(ctx)
                else:
                    logger.debug(f"Filtered out repetitive context: {content[:100]}...")

            except Exception as e:
                logger.error(f"Error filtering context: {str(e)}")
                # If there's an error filtering, include the context to not break functionality
                filtered_contexts.append(ctx)

        logger.debug(f"Filtered {len(contexts) - len(filtered_contexts)} repetitive contexts out of {len(contexts)} total")
        return filtered_contexts

    def _remove_repetitive_content(self, text: str) -> str:
        """
        Remove repetitive content from text to prevent duplication
        """
        if not text or not isinstance(text, str):
            return text if text is not None else ""

        try:
            lines = text.split('\n')
            seen_lines = set()
            unique_lines = []

            for line in lines:
                line_stripped = line.strip()
                if line_stripped and line_stripped not in seen_lines:
                    seen_lines.add(line_stripped)
                    unique_lines.append(line)

            result = '\n'.join(unique_lines)
            return result
        except Exception as e:
            logger.error(f"Error in _remove_repetitive_content: {str(e)}")
            return text  # Return original text if processing fails

    def validate_citations(self, citations: List[Citation], retrieved_contexts: List[RetrievedContext]) -> Dict[str, Any]:
        """
        Validate that all responses include proper source citations
        """
        logger.info("Validating citations...")

        validation_result = {
            "valid": True,
            "citation_count": len(citations),
            "context_count": len(retrieved_contexts),
            "citations_match_contexts": len(citations) == len(retrieved_contexts),
            "all_citations_complete": True,
            "missing_fields": [],
            "details": []
        }

        if not citations:
            validation_result["valid"] = False
            validation_result["all_citations_complete"] = False
            validation_result["details"].append("No citations provided")
            return validation_result

        # Check each citation for completeness
        for i, citation in enumerate(citations):
            missing_fields = []

            if not citation.source_url:
                missing_fields.append("source_url")
            if not citation.chapter:
                missing_fields.append("chapter")
            if not citation.section:
                missing_fields.append("section")

            if missing_fields:
                validation_result["all_citations_complete"] = False
                validation_result["valid"] = False
                validation_result["missing_fields"].extend(missing_fields)
                validation_result["details"].append(f"Citation {i} missing fields: {missing_fields}")

        # Check that citations correspond to retrieved contexts
        if len(citations) > 0 and len(retrieved_contexts) > 0:
            # Verify that citation sources match context sources
            citation_urls = {c.source_url for c in citations}
            context_urls = {c.url for c in retrieved_contexts}
            urls_match = citation_urls == context_urls

            validation_result["urls_match"] = urls_match
            if not urls_match:
                validation_result["valid"] = False
                validation_result["details"].append(f"Source URLs don't match: citations={citation_urls}, contexts={context_urls}")

        logger.info(f"Citation validation result: {validation_result}")
        return validation_result


# Global instance of the textbook agent
textbook_agent = TextbookAgent()