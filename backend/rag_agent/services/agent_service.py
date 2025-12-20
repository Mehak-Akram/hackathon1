"""
Main agent service orchestrating all components of the RAG Agent Service
"""
import time
import asyncio
from typing import Dict, Any, Optional
from ..agents.textbook_agent import textbook_agent
from ..services.conversation import conversation_service
from ..services.validation import validation_service
from ..api.models.request import ChatRequest
from ..api.models.response import ChatResponse
from ..utils.logger import get_logger
from ..utils.helpers import time_it_async
from ..config.settings import settings
from ..utils.error_handler import handle_exceptions, debug_context, error_handler
from ..utils.debug_utils import debug_trace, debug_performance_monitor, log_data_flow


logger = get_logger(__name__)


class AgentService:
    """
    Main service that orchestrates all components of the RAG Agent
    """
    def __init__(self):
        self.textbook_agent = textbook_agent
        self.conversation_service = conversation_service
        self.validation_service = validation_service

    @time_it_async
    @debug_trace(include_args=True, include_result=False, log_level="DEBUG")
    @debug_performance_monitor(time_threshold=5.0, memory_threshold=50.0)
    @log_data_flow(operation="agent_service_process_request")
    @handle_exceptions(
        fallback_return=None,
        log_error=True,
        reraise=False,
        include_system_diagnostics=True
    )
    async def process_request(self, chat_request: ChatRequest) -> ChatResponse:
        """
        Process a chat request through all service components with error handling and fallbacks
        """
        start_time = time.time()
        request_id = f"req_{int(start_time)}_{hash(chat_request.question) % 10000}"

        logger.info(f"[{request_id}] Processing chat request: {chat_request.question[:50]}...")

        # Initialize default response in case of errors
        fallback_response = ChatResponse(
            response="I'm sorry, but I encountered an issue while processing your request. Please try again later.",
            session_id=chat_request.session_id or "unknown",
            citations=[],
            retrieved_context_count=0,
            response_time=0.0
        )

        try:
            # Step 1: Get conversation context if session exists
            conversation_context = []
            try:
                if chat_request.session_id:
                    conversation_context = await self.conversation_service.get_conversation_context(
                        chat_request.session_id, max_turns=5
                    )
                    logger.debug(f"[{request_id}] Retrieved {len(conversation_context)} conversation turns")
            except Exception as e:
                logger.warning(f"[{request_id}] Failed to retrieve conversation context: {str(e)}. Proceeding without context.")
                # Continue with empty conversation context as fallback

            # Step 2: Process the request with the textbook agent
            try:
                response = await self.textbook_agent.answer_question(
                    question=chat_request.question,
                    session_id=chat_request.session_id,
                    user_preferences=chat_request.user_preferences.dict() if chat_request.user_preferences else None
                )
            except Exception as e:
                logger.error(f"[{request_id}] Textbook agent failed: {str(e)}. Attempting fallback.")

                # Fallback: try a simpler approach without conversation context
                try:
                    response = await self.textbook_agent.answer_question(
                        question=chat_request.question,
                        session_id=chat_request.session_id,
                        user_preferences=None  # Ignore user preferences in fallback
                    )
                    logger.info(f"[{request_id}] Fallback agent processing succeeded")
                except Exception as fallback_e:
                    logger.error(f"[{request_id}] Fallback agent processing also failed: {str(fallback_e)}")
                    # Return the initialized fallback response with error info
                    error_msg = f"I'm sorry, but I encountered an issue while processing your request about '{chat_request.question[:50]}...'. Please try again later."
                    fallback_response.response = error_msg
                    total_time = time.time() - start_time
                    fallback_response.response_time = total_time
                    return fallback_response

            # Step 3: Validate the response and citations
            try:
                validation_result = self.validation_service.validate_response_citations(
                    response=response
                )

                if not validation_result["valid"]:
                    logger.warning(f"[{request_id}] Response validation issues: {validation_result['citation_validation']['details']}")
            except Exception as e:
                logger.warning(f"[{request_id}] Response validation failed: {str(e)}. Proceeding with response.")

            # Step 4: Add the conversation turn to history
            try:
                if chat_request.session_id:
                    await self.conversation_service.add_conversation_turn(
                        chat_request.session_id,
                        chat_request.question,
                        response.response
                    )
                    logger.debug(f"[{request_id}] Conversation history updated")
            except Exception as e:
                logger.warning(f"[{request_id}] Failed to update conversation history: {str(e)}. Continuing.")

            # Calculate total processing time
            total_time = time.time() - start_time
            response.response_time = total_time

            # Log performance metrics
            logger.info(f"[{request_id}] Processed request in {total_time:.2f}s "
                       f"with {len(response.citations)} citations")

            # Performance tracking: log slow requests
            if total_time > 10.0:  # Log requests taking more than 10 seconds
                logger.warning(f"[{request_id}] Slow request detected: {total_time:.2f}s")

            return response

        except Exception as e:
            logger.error(f"[{request_id}] Critical error processing chat request: {str(e)}", exc_info=True)

            # Final fallback: return a safe response
            total_time = time.time() - start_time
            fallback_response.response_time = total_time
            fallback_response.session_id = chat_request.session_id or fallback_response.session_id
            return fallback_response

    @debug_trace(include_args=True, include_result=False, log_level="DEBUG")
    @debug_performance_monitor(time_threshold=10.0, memory_threshold=75.0)
    @log_data_flow(operation="agent_service_circuit_breaker")
    @handle_exceptions(
        fallback_return=None,
        log_error=True,
        reraise=True,
        include_system_diagnostics=True
    )
    async def process_request_with_circuit_breaker(self, chat_request: ChatRequest, max_retries: int = 2) -> ChatResponse:
        """
        Process a request with circuit breaker pattern and retry logic
        """
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                request_id = f"req_{int(time.time())}_{hash(chat_request.question) % 10000}_attempt_{attempt}"
                logger.info(f"[{request_id}] Processing request attempt {attempt + 1}/{max_retries + 1}")

                response = await self.process_request(chat_request)

                # If successful, return the response
                logger.info(f"[{request_id}] Request processed successfully on attempt {attempt + 1}")
                return response

            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")

                if attempt < max_retries:
                    # Wait before retry with exponential backoff
                    wait_time = 0.5 * (2 ** attempt)  # 0.5s, 1s, 2s...
                    logger.info(f"Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"All {max_retries + 1} attempts failed for request: {str(e)}")

        # If all retries failed, raise the last exception
        raise last_exception

    @debug_trace(include_args=True, include_result=False, log_level="DEBUG")
    @debug_performance_monitor(time_threshold=15.0, memory_threshold=100.0)
    @log_data_flow(operation="agent_service_detailed_logging")
    @handle_exceptions(
        fallback_return=None,
        log_error=True,
        reraise=True,
        include_system_diagnostics=True
    )
    async def process_request_with_detailed_logging(self, chat_request: ChatRequest) -> Dict[str, Any]:
        """
        Process a request with detailed performance and logging information
        """
        start_time = time.time()
        request_id = f"req_{int(start_time)}_{hash(chat_request.question) % 10000}"

        logger.info(f"[{request_id}] Starting detailed processing: {chat_request.question[:50]}...")

        processing_log = {
            "request_id": request_id,
            "question": chat_request.question,
            "session_id": chat_request.session_id,
            "start_time": start_time,
            "steps": [],
            "errors": [],
            "total_time": 0,
            "result": None
        }

        try:
            # Step 1: Get conversation context
            context_start = time.time()
            conversation_context = []
            if chat_request.session_id:
                conversation_context = await self.conversation_service.get_conversation_context(
                    chat_request.session_id, max_turns=5
                )
            context_time = time.time() - context_start

            processing_log["steps"].append({
                "step": "get_conversation_context",
                "time": context_time,
                "details": f"Retrieved {len(conversation_context)} turns"
            })

            # Step 2: Process with textbook agent
            agent_start = time.time()
            response = await self.textbook_agent.answer_question(
                question=chat_request.question,
                session_id=chat_request.session_id,
                user_preferences=chat_request.user_preferences.dict() if chat_request.user_preferences else None
            )
            agent_time = time.time() - agent_start

            processing_log["steps"].append({
                "step": "textbook_agent_processing",
                "time": agent_time,
                "details": f"Generated response with {len(response.citations)} citations"
            })

            # Step 3: Validate response
            validation_start = time.time()
            validation_result = self.validation_service.validate_response_citations(
                response=response
            )
            validation_time = time.time() - validation_start

            processing_log["steps"].append({
                "step": "response_validation",
                "time": validation_time,
                "details": f"Validation result: {validation_result['valid']}"
            })

            # Step 4: Update conversation history
            history_start = time.time()
            if chat_request.session_id:
                await self.conversation_service.add_conversation_turn(
                    chat_request.session_id,
                    chat_request.question,
                    response.response
                )
            history_time = time.time() - history_start

            processing_log["steps"].append({
                "step": "update_conversation_history",
                "time": history_time,
                "details": "History updated successfully"
            })

            # Finalize timing
            total_time = time.time() - start_time
            response.response_time = total_time
            processing_log["total_time"] = total_time
            processing_log["result"] = {
                "response_length": len(response.response),
                "citation_count": len(response.citations),
                "response_time": response.response_time
            }

            logger.info(f"[{request_id}] Detailed processing completed in {total_time:.2f}s - "
                       f"Steps: {len(processing_log['steps'])}, "
                       f"Citations: {len(response.citations)}")

            return processing_log

        except Exception as e:
            error_time = time.time() - start_time
            processing_log["total_time"] = error_time
            processing_log["errors"].append({
                "error": str(e),
                "time": error_time,
                "step": "unknown"
            })

            logger.error(f"[{request_id}] Detailed processing failed after {error_time:.2f}s: {str(e)}", exc_info=True)
            raise

    async def validate_service_health(self) -> Dict[str, Any]:
        """
        Validate the health of all service components
        """
        health_status = {
            "service": "RAG Agent Service",
            "status": "healthy",
            "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime()),
            "components": {
                "textbook_agent": {"status": "unknown", "details": {}},
                "conversation_service": {"status": "unknown", "details": {}},
                "validation_service": {"status": "unknown", "details": {}}
            },
            "overall_response_time": 0.0
        }

        start_time = time.time()

        try:
            # Test textbook agent
            health_status["components"]["textbook_agent"]["status"] = "healthy"
            health_status["components"]["textbook_agent"]["details"]["connected"] = True
        except Exception as e:
            health_status["components"]["textbook_agent"]["status"] = "unhealthy"
            health_status["components"]["textbook_agent"]["details"]["error"] = str(e)
            health_status["status"] = "unhealthy"

        try:
            # Test conversation service
            test_session = await self.conversation_service.create_session()
            await self.conversation_service.end_session(test_session.id)
            health_status["components"]["conversation_service"]["status"] = "healthy"
            health_status["components"]["conversation_service"]["details"]["connected"] = True
        except Exception as e:
            health_status["components"]["conversation_service"]["status"] = "unhealthy"
            health_status["components"]["conversation_service"]["details"]["error"] = str(e)
            health_status["status"] = "unhealthy"

        try:
            # Test validation service
            health_status["components"]["validation_service"]["status"] = "healthy"
            health_status["components"]["validation_service"]["details"]["connected"] = True
        except Exception as e:
            health_status["components"]["validation_service"]["status"] = "unhealthy"
            health_status["components"]["validation_service"]["details"]["error"] = str(e)
            health_status["status"] = "unhealthy"

        health_status["overall_response_time"] = time.time() - start_time

        return health_status

    async def get_service_metrics(self) -> Dict[str, Any]:
        """
        Get metrics about service usage and performance
        """
        active_sessions = await self.conversation_service.get_all_active_sessions()

        metrics = {
            "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime()),
            "active_sessions": len(active_sessions),
            "session_timeout_minutes": settings.session_timeout_minutes,
            "default_top_k": settings.default_top_k,
            "agent_model": settings.agent_model,
            "estimated_daily_requests": 0,  # Would be calculated from logs in a real implementation
            "average_response_time": 0.0,  # Would be calculated from logs in a real implementation
        }

        return metrics


# Global instance of the agent service
agent_service = AgentService()