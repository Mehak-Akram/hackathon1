"""
Chat API routes for the RAG Agent Service
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import time
import uuid

from ...api.models.request import ChatRequest
from ...api.models.response import ChatResponse, ErrorResponse
from ...services.agent_service import agent_service
from ...utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/chat",
             response_model=ChatResponse,
             summary="Submit a question to the RAG agent",
             description="Sends a user question to the agent and receives a textbook-grounded response")
async def chat_endpoint(
    chat_request: ChatRequest
) -> ChatResponse:
    """
    Submit a question to the RAG agent without database logging (stateless)
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

        # Process the question with the agent service (stateless operation)
        response = await agent_service.process_request(chat_request=chat_request)

        # Ensure response time is properly set (minimum 0.001 to avoid validation errors)
        total_time = time.time() - start_time
        if response.response_time <= 0:
            response.response_time = max(total_time, 0.001)

        logger.info(f"Chat request completed in {total_time:.3f}s")

        return response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        # Return a proper ChatResponse instead of raising an exception
        total_time = time.time() - start_time
        error_msg = "An error occurred while processing your question. Please try again."
        return ChatResponse(
            response=error_msg,
            citations=[],
            retrieved_context_count=0,
            response_time=max(total_time, 0.001)  # Ensure minimum response time
        )