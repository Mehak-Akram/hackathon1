"""
FastAPI server for the Gemini AI Agent.
Provides a REST API interface for interacting with the Gemini agent.
"""
import os
import asyncio
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

from src.agents.gemini_agent import GeminiAgent
from src.utils.config_loader import load_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Gemini AI Agent API",
    description="REST API for interacting with the Gemini AI Agent",
    version="1.0.0"
)

# Request/Response models
class MessageRequest(BaseModel):
    message: str
    model: Optional[str] = "gemini-2.0-flash"
    temperature: Optional[float] = 0.7

class MessageResponse(BaseModel):
    response: str
    model_used: str
    success: bool
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    model: str
    tracing_disabled: bool

# Global agent instance
agent: Optional[GeminiAgent] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the Gemini agent when the server starts."""
    global agent
    try:
        # Load configuration to verify API key is available
        config = load_config()
        logger.info(f"Configuration loaded successfully. Model: {config['model']}")

        # Initialize the agent
        agent = GeminiAgent()
        logger.info("GeminiAgent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize GeminiAgent: {str(e)}")
        raise

@app.get("/")
async def root():
    """Root endpoint for basic server information."""
    return {
        "message": "Gemini AI Agent API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    return HealthResponse(
        status="healthy",
        model=agent.model,
        tracing_disabled=agent.config.tracing_enabled is False
    )

@app.post("/chat", response_model=MessageResponse)
async def chat(request: MessageRequest):
    """Chat endpoint to interact with the Gemini agent."""
    global agent

    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        # Run the agent with the provided message
        response = await agent.run(request.message)

        return MessageResponse(
            response=response,
            model_used=agent.model,
            success=True
        )
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.post("/chat/stream")
async def chat_stream(request: MessageRequest):
    """Streaming chat endpoint (placeholder - basic implementation)."""
    global agent

    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        # For now, just return the regular response
        # In a full implementation, this would use Server-Sent Events or WebSockets
        response = await agent.run(request.message)

        # This is a simplified streaming response - in a real implementation
        # you would use StreamingResponse with Server-Sent Events
        return {"response": response, "model_used": agent.model}
    except Exception as e:
        logger.error(f"Error processing streaming chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )