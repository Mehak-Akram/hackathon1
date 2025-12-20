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
from ..utils.error_handler import handle_exceptions, debug_context, error_handler
from ..utils.debug_utils import debug_trace, debug_performance_monitor, log_data_flow
from ..utils.logger import get_logger
from ..utils.error_handler import error_handler
from .retrieval_tool import retrieval_tool
from ..utils.connection_pool import get_http_client
from ..services.conversation import conversation_service
from ..utils.performance import (
    cached_agent_response,
    optimize_concurrent_retrieval,
    measure_performance,
    async_timeout,
    apply_optimized_settings,
    OPTIMIZED_SETTINGS
)

logger = get_logger(__name__)


class TextbookAgent:
    """
    AI agent that answers questions about Physical AI concepts using textbook content
    """
    def __init__(self):
        # Use Google Gemini via OpenAI-compatible endpoint instead of OpenAI
        # This maintains the same interface while using Gemini's free tier
        if settings.gemini_api_key:
            # Use Gemini API with OpenAI-compatible endpoint
            self.client = AsyncOpenAI(
                api_key=settings.gemini_api_key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
            )
            self.model = "gemini-2.0-flash"  # Use free tier model
        else:
            # Fallback to OpenAI if no Gemini key provided
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
            self.model = settings.agent_model  # Use configured model
        self.retrieval_tool = retrieval_tool
        self.conversation_service = conversation_service

    @measure_performance
    @cached_agent_response(ttl=300)  # Cache responses for 5 minutes
    @optimize_concurrent_retrieval
    @async_timeout(10.0)  # 10 second timeout for the entire operation
    @debug_trace(include_args=True, include_result=False, log_level="DEBUG")
    @debug_performance_monitor(time_threshold=2.0, memory_threshold=25.0)
    @log_data_flow(operation="answer_question")
    @handle_exceptions(
        fallback_return=None,
        log_error=True,
        reraise=True,
        include_system_diagnostics=True
    )
    async def answer_question(
        self,
        question: str,
        session_id: Optional[str] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> ChatResponse:
        """
        Answer a question using retrieved textbook content and conversation context
        Optimized for sub-10 second response time with caching and performance monitoring
        """
        start_time = time.time()
        logger.info(f"Processing question: {question[:50]}... for session {session_id}")

        try:
            # Get conversation context if session is provided
            conversation_context = []
            if session_id:
                try:
                    conversation_context = await self.conversation_service.get_conversation_context(
                        session_id, max_turns=5
                    )
                    logger.debug(f"Retrieved {len(conversation_context)} conversation turns for session {session_id}")
                except Exception as e:
                    error_id = log_error_with_context(e, {
                        "operation": "get_conversation_context",
                        "session_id": session_id,
                        "question": question[:50]
                    })
                    logger.warning(f"Failed to retrieve conversation context: {str(e)} - Error ID: {error_id}")
                    # Continue with empty conversation context

            # Retrieve relevant context from the textbook with optimized parameters
            retrieved_contexts = await self.retrieval_tool.retrieve_context(
                query=question,
                top_k=min(settings.default_top_k, 5)  # Limit to 5 for faster retrieval
            )

            # Generate the answer using the retrieved context and conversation history
            response_content = await self._generate_answer_with_context(
                question,
                retrieved_contexts,
                user_preferences,
                conversation_context=conversation_context
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

            # Calculate response time
            response_time = time.time() - start_time

            # Create the chat response
            chat_response = ChatResponse(
                response=response_content,
                session_id=session_id or "unknown",
                citations=citations,
                retrieved_context_count=len(retrieved_contexts),
                response_time=response_time
            )

            # Add the conversation turn to the session history if session_id is provided
            if session_id:
                try:
                    await self.conversation_service.add_conversation_turn(
                        session_id, question, response_content
                    )
                    logger.debug(f"Added conversation turn to session {session_id}")
                except Exception as e:
                    error_id = log_error_with_context(e, {
                        "operation": "add_conversation_turn",
                        "session_id": session_id,
                        "question": question[:50]
                    })
                    logger.warning(f"Failed to add conversation turn: {str(e)} - Error ID: {error_id}")

            logger.info(f"Generated response in {response_time:.2f}s with {len(citations)} citations")
            return chat_response

        except asyncio.TimeoutError:
            error_id = log_error_with_context(asyncio.TimeoutError(f"Timeout processing question: {question[:50]}..."), {
                "operation": "answer_question",
                "session_id": session_id,
                "question": question[:50]
            })
            logger.error(f"Timeout processing question: {question[:50]}... - Error ID: {error_id}")
            # Return a helpful response instead of failing
            return ChatResponse(
                response="I'm sorry, but I'm taking too long to process your question. Please try rephrasing or ask a more specific question.",
                session_id=session_id or "unknown",
                citations=[],
                retrieved_context_count=0,
                response_time=time.time() - start_time
            )
        except Exception as e:
            error_id = log_error_with_context(e, {
                "operation": "answer_question",
                "session_id": session_id,
                "question": question[:50]
            })
            logger.error(f"Error answering question '{question[:30]}...': {str(e)} - Error ID: {error_id}")
            # Return a graceful error response instead of raising exception
            # This allows the API route to return a proper response instead of an HTTP error
            return ChatResponse(
                response="I'm sorry, but I encountered an error while processing your question. Please try again.",
                session_id=session_id or "unknown",
                citations=[],
                retrieved_context_count=0,
                response_time=time.time() - start_time
            )

    @debug_trace(include_args=False, include_result=False, log_level="DEBUG")
    @log_data_flow(operation="generate_answer_with_context")
    @handle_exceptions(
        fallback_return="I encountered an error while generating a response. Please try again.",
        log_error=True,
        reraise=False,
        include_system_diagnostics=True
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

        # If no contexts after filtering or originally empty, provide a general response
        if not filtered_contexts:
            logger.info(f"No relevant contexts found for question: {question[:50]}...")
            # Use the LLM to answer based on its general knowledge, but with appropriate disclaimer
            prompt = f"Question: {question}\n\nYou are an AI assistant. I couldn't find specific textbook content relevant to this question. Provide a general answer if possible, or explain that you don't have specific textbook information for this query."

            try:
                messages = [
                    {
                        "role": "system",
                        "content": (
                            "You are an expert assistant for a Physical AI textbook. "
                            "If you have specific information from the textbook context provided, use that. "
                            "If no context is provided, you may use your general knowledge to provide a helpful response, "
                            "but acknowledge that it's not from the specific textbook content."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]

                try:
                    response = await self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        max_tokens=settings.max_response_tokens,
                        temperature=settings.temperature
                    )

                    if not response or not hasattr(response, 'choices') or not response.choices:
                        logger.warning("Empty or invalid response from LLM in fallback")
                        return f"I understand you're asking about '{question}'. I don't have specific textbook content for this query, but I'm here to help. Could you try rephrasing your question?"

                    first_choice = response.choices[0]
                    if not hasattr(first_choice, 'message') or not hasattr(first_choice.message, 'content'):
                        logger.warning("Response choice missing message content in fallback")
                        return f"I understand you're asking about '{question}'. I don't have specific textbook content for this query, but I'm here to help. Could you try rephrasing your question?"

                    answer = first_choice.message.content
                except Exception as llm_error:
                    logger.error(f"Error calling LLM API in fallback: {str(llm_error)}")
                    # Provide a helpful response without depending on the LLM
                    return f"I understand you're asking about '{question}'. I don't have specific textbook content for this query, but I'm here to help. Could you try rephrasing your question?"

                if answer:
                    answer = answer.strip()
                else:
                    answer = f"I understand you're asking about '{question}'. I don't have specific textbook content for this query, but I'm here to help. Could you try rephrasing your question?"

                logger.debug(f"Generated general answer: {answer[:100] if answer else 'None'}...")
                return answer
            except Exception as e:
                logger.error(f"Error generating general answer: {str(e)}")
                return f"I understand you're asking about '{question}'. I don't have specific textbook content for this query, but I'm here to help. Could you try rephrasing your question?"

        # Format the retrieved contexts for the LLM
        formatted_context = self._format_context_for_llm(filtered_contexts)

        # Format the conversation history if provided
        formatted_conversation = ""
        if conversation_context:
            formatted_conversation = self._format_conversation_history(conversation_context)

        # Build the prompt with context
        detail_level = (user_preferences or {}).get('detail_level', 'intermediate')
        response_format = (user_preferences or {}).get('response_format', 'detailed')

        prompt = self._build_prompt(
            question=question,
            context=formatted_context,
            conversation_history=formatted_conversation,
            detail_level=detail_level,
            response_format=response_format
        )

        try:
            # Call OpenAI API to generate the response
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an expert assistant for a Physical AI textbook. "
                        "Answer questions based ONLY on the provided context from the textbook. "
                        "Do not hallucinate or provide information outside the provided context. "
                        "Always provide source citations for the information you provide. "
                        "Consider the conversation history when answering follow-up questions."
                        "IMPORTANT: Do not repeat or include repetitive phrases like 'Complete Learning Path' multiple times in your response."
                    )
                }
            ]

            # Add conversation history to the messages if available
            if formatted_conversation:
                messages.append({
                    "role": "system",
                    "content": f"Previous conversation:\n{formatted_conversation}"
                })

            messages.append({
                "role": "user",
                "content": prompt
            })

            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=settings.max_response_tokens,
                    temperature=settings.temperature
                )
            except Exception as llm_error:
                logger.error(f"Error calling LLM API: {str(llm_error)}")
                # Return a helpful response instead of failing completely
                return "I'm sorry, but I'm having trouble connecting to the AI service right now. Please try again later."

            # Handle potential issues with the response structure
            try:
                if not response or not hasattr(response, 'choices') or not response.choices:
                    logger.warning("Empty or invalid response from LLM")
                    return "I'm sorry, but I couldn't generate a response for your question."

                first_choice = response.choices[0]
                if not hasattr(first_choice, 'message') or not hasattr(first_choice.message, 'content'):
                    logger.warning("Response choice missing message content")
                    return "I'm sorry, but I couldn't generate a response for your question."

                answer = first_choice.message.content
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
            except Exception as response_error:
                logger.error(f"Error processing LLM response: {str(response_error)}")
                return "I'm sorry, but I had trouble processing the response. Please try again."

        except Exception as e:
            error_id = log_error_with_context(e, {
                "operation": "openai_api_call",
                "question": question[:50],
                "model": settings.agent_model
            })
            logger.error(f"Error calling OpenAI API: {str(e)} - Error ID: {error_id}")
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
        conversation_history: str = "",
        detail_level: str = "intermediate",
        response_format: str = "detailed"
    ) -> str:
        """
        Build the prompt for the LLM based on user preferences and conversation history
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

        if conversation_history:
            prompt = (
                f"Based on the following textbook content and conversation history, please answer the question.\n\n"
                f"TEXTBOOK CONTENT:\n{context}\n\n"
                f"CONVERSATION HISTORY:\n{conversation_history}\n\n"
                f"QUESTION: {question}\n\n"
                f"INSTRUCTIONS:\n"
                f"- Answer only based on the provided textbook content\n"
                f"- Do not provide information not found in the textbook\n"
                f"- Always cite the source of your information\n"
                f"- Consider the conversation history when answering follow-up questions\n"
                f"- {detail_instructions.get(detail_level, detail_instructions['intermediate'])}\n"
                f"- {format_instructions.get(response_format, format_instructions['detailed'])}\n"
                f"- If the textbook content doesn't contain the answer, clearly state that\n"
            )
        else:
            prompt = (
                f"Based on the following textbook content, please answer the question.\n\n"
                f"TEXTBOOK CONTENT:\n{context}\n\n"
                f"QUESTION: {question}\n\n"
                f"INSTRUCTIONS:\n"
                f"- Answer only based on the provided textbook content\n"
                f"- Do not provide information not found in the textbook\n"
                f"- Always cite the source of your information\n"
                f"- {detail_instructions.get(detail_level, detail_instructions['intermediate'])}\n"
                f"- {format_instructions.get(response_format, format_instructions['detailed'])}\n"
                f"- If the textbook content doesn't contain the answer, clearly state that\n"
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

    @debug_trace(include_args=False, include_result=False, log_level="DEBUG")
    @log_data_flow(operation="validate_answer_grounding")
    @handle_exceptions(
        fallback_return=False,
        log_error=True,
        reraise=False,
        include_system_diagnostics=True
    )
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

    @debug_trace(include_args=False, include_result=False, log_level="DEBUG")
    @log_data_flow(operation="validate_citations")
    @handle_exceptions(
        fallback_return={"valid": False, "details": ["Error occurred during citation validation"]},
        log_error=True,
        reraise=False,
        include_system_diagnostics=True
    )
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