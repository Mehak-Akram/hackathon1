"""
Chat API routes for the RAG Agent Service
"""
from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any
import time
import uuid

from ...api.models.request import ChatRequest, SessionRequest
from ...api.models.response import ChatResponse, SessionResponse, ErrorResponse
from ...agents.textbook_agent import textbook_agent
from ...utils.logger import get_logger
from ...utils.helpers import is_valid_uuid
from ...config.settings import settings
from ...utils.error_handler import handle_exceptions, debug_context, error_handler
from ...utils.debug_utils import debug_trace, debug_performance_monitor, log_data_flow

router = APIRouter()
logger = get_logger(__name__)

# In-memory session storage (in production, use Redis or database)
active_sessions: Dict[str, Dict[str, Any]] = {}


@router.post("/chat",
             response_model=ChatResponse,
             summary="Submit a question to the RAG agent",
             description="Sends a user question to the agent and receives a textbook-grounded response")
@debug_trace(include_args=True, include_result=False, log_level="DEBUG")
@debug_performance_monitor(time_threshold=10.0, memory_threshold=50.0)
@log_data_flow(operation="api_chat_endpoint")
@handle_exceptions(
    fallback_return=None,
    log_error=True,
    reraise=True,
    include_system_diagnostics=True
)
async def chat_endpoint(chat_request: ChatRequest) -> ChatResponse:
    """
    Submit a question to the RAG agent
    """
    start_time = time.time()
    request_id = str(uuid.uuid4())

    # Set the request ID in context for logging
    from ...utils.logger import request_id_var
    request_id_var.set(request_id)

    logger.info(f"Processing chat request: {chat_request.question[:50]}...")

    try:
        # Validate the request
        if not chat_request.question or not chat_request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")

        # Use provided session ID or create a new one
        session_id = chat_request.session_id
        if not session_id:
            session_id = str(uuid.uuid4())
            # Initialize new session
            active_sessions[session_id] = {
                "created_at": time.time(),
                "last_activity": time.time(),
                "conversation_history": []
            }
        elif session_id not in active_sessions:
            # If session doesn't exist, create it
            active_sessions[session_id] = {
                "created_at": time.time(),
                "last_activity": time.time(),
                "conversation_history": []
            }

        # Update last activity for the session
        active_sessions[session_id]["last_activity"] = time.time()

        # Process the question with the textbook agent
        response = await textbook_agent.answer_question(
            question=chat_request.question,
            session_id=session_id,
            user_preferences=chat_request.user_preferences.dict() if chat_request.user_preferences else None
        )

        # Update response with the correct session ID
        response.session_id = session_id

        # Calculate total response time
        total_time = time.time() - start_time
        logger.info(f"Chat request completed in {total_time:.2f}s")

        # Update response time to include processing time
        response.response_time = total_time

        return response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        error_response = ErrorResponse(
            error="AGENT_ERROR",
            message="An error occurred while processing your question"
        )
        raise HTTPException(status_code=500, detail=error_response.dict())


@router.post("/session",
             response_model=SessionResponse,
             summary="Create a new conversation session",
             description="Initializes a new conversation session for multi-turn interactions")
@debug_trace(include_args=True, include_result=False, log_level="DEBUG")
@debug_performance_monitor(time_threshold=1.0, memory_threshold=10.0)
@log_data_flow(operation="api_create_session")
@handle_exceptions(
    fallback_return=None,
    log_error=True,
    reraise=True,
    include_system_diagnostics=True
)
async def create_session(session_request: SessionRequest = None) -> SessionResponse:
    """
    Create a new conversation session
    """
    if session_request is None:
        session_request = SessionRequest()

    session_id = str(uuid.uuid4())

    # Create new session
    active_sessions[session_id] = {
        "created_at": time.time(),
        "last_activity": time.time(),
        "user_id": session_request.user_id,
        "metadata": session_request.metadata or {},
        "conversation_history": []
    }

    logger.info(f"Created new session: {session_id}")

    return SessionResponse(
        session_id=session_id,
        created_at=time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime()),
    )


@router.get("/session/{session_id}",
            summary="Get session information",
            description="Retrieves information about an active session")
@debug_trace(include_args=True, include_result=False, log_level="DEBUG")
@debug_performance_monitor(time_threshold=0.5, memory_threshold=5.0)
@log_data_flow(operation="api_get_session")
@handle_exceptions(
    fallback_return=None,
    log_error=True,
    reraise=True,
    include_system_diagnostics=True
)
async def get_session(session_id: str) -> Dict[str, Any]:
    """
    Get session information
    """
    if not is_valid_uuid(session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session_data = active_sessions[session_id]

    return {
        "session_id": session_id,
        "active": True,
        "created_at": session_data["created_at"],
        "last_activity": session_data["last_activity"],
        "user_id": session_data.get("user_id"),
        "metadata": session_data.get("metadata"),
        "conversation_count": len(session_data["conversation_history"])
    }


@router.delete("/session/{session_id}",
               summary="End a conversation session",
               description="Ends and cleans up a conversation session")
@debug_trace(include_args=True, include_result=False, log_level="DEBUG")
@debug_performance_monitor(time_threshold=0.5, memory_threshold=5.0)
@log_data_flow(operation="api_end_session")
@handle_exceptions(
    fallback_return=None,
    log_error=True,
    reraise=True,
    include_system_diagnostics=True
)
async def end_session(session_id: str) -> Dict[str, str]:
    """
    End a conversation session
    """
    if not is_valid_uuid(session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    del active_sessions[session_id]
    logger.info(f"Ended session: {session_id}")

    return {"message": f"Session {session_id} ended successfully"}


# Add middleware to clean up expired sessions periodically
@debug_trace(include_args=False, include_result=False, log_level="DEBUG")
@debug_performance_monitor(time_threshold=2.0, memory_threshold=10.0)
@log_data_flow(operation="api_cleanup_sessions")
@handle_exceptions(
    fallback_return=None,
    log_error=True,
    reraise=False,
    include_system_diagnostics=True
)
async def cleanup_expired_sessions():
    """
    Clean up sessions that have exceeded the timeout
    """
    current_time = time.time()
    expired_sessions = []

    for session_id, session_data in active_sessions.items():
        time_since_last_activity = current_time - session_data["last_activity"]
        if time_since_last_activity > (settings.session_timeout_minutes * 60):
            expired_sessions.append(session_id)

    for session_id in expired_sessions:
        del active_sessions[session_id]
        logger.info(f"Cleaned up expired session: {session_id}")