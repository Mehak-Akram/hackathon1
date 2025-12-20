"""
FastAPI server for the Gemini AI Agent.
"""
import asyncio
import os
import uuid
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .agents.gemini_agent import GeminiAgent
from .utils.logger import logger

app = FastAPI(
    title="Gemini AI Agent API",
    description="API for interacting with the Gemini AI Agent",
    version="1.0.0"
)

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the agent
agent = GeminiAgent()

# In-memory storage for sessions (in production, use a database)
sessions = {}

class MessageRequest(BaseModel):
    message: str

class SessionRequest(BaseModel):
    user_id: str = None

class SessionResponse(BaseModel):
    session_id: str
    created_at: datetime

class MessageResponse(BaseModel):
    response: str

@app.get("/")
async def root():
    """Root endpoint to check if the server is running."""
    return {"message": "Gemini AI Agent API is running!"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.post("/api/v1/session", response_model=SessionResponse)
async def create_session(request: SessionRequest):
    """
    Create a new chat session.
    """
    try:
        session_id = str(uuid.uuid4())
        created_at = datetime.now()

        sessions[session_id] = {
            "user_id": request.user_id,
            "created_at": created_at,
            "messages": []
        }

        logger.info(f"Created new session: {session_id}")
        return SessionResponse(session_id=session_id, created_at=created_at)
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/chat", response_model=MessageResponse)
async def chat(request: MessageRequest):
    """
    Chat endpoint to interact with the Gemini AI Agent.
    """
    try:
        logger.info(f"Received message: {request.message}")
        response = await agent.run(request.message)
        logger.info(f"Sending response: {response}")
        return MessageResponse(response=response)
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Keep the original /chat endpoint for compatibility
@app.post("/chat", response_model=MessageResponse)
async def chat_legacy(request: MessageRequest):
    """
    Legacy chat endpoint to interact with the Gemini AI Agent.
    """
    try:
        logger.info(f"Received message: {request.message}")
        response = await agent.run(request.message)
        logger.info(f"Sending response: {response}")
        return MessageResponse(response=response)
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)