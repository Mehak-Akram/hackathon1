"""
Main FastAPI application for the RAG Agent Service for Physical AI Textbook
"""
import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("rag_agent.log", mode="a")
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan manager for startup and shutdown events
    """
    logger.info("Starting RAG Agent Service for Physical AI Textbook")
    yield
    logger.info("Shutting down RAG Agent Service for Physical AI Textbook")

# Create FastAPI app
app = FastAPI(
    title="RAG Agent Service for Physical AI Textbook",
    description="API for interacting with the Physical AI Textbook RAG Agent",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify the service is running
    """
    return {"status": "healthy", "service": "RAG Agent Service"}

@app.get("/")
async def root():
    """
    Root endpoint providing basic information about the service
    """
    return {
        "message": "RAG Agent Service for Physical AI Textbook",
        "version": "1.0.0",
        "endpoints": ["/health", "/api/v1/chat", "/api/v1/chat/session"]
    }

# Include API routes
try:
    import sys
    import os
    # Add the backend directory to the Python path to resolve imports properly
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    # Import using absolute path
    from rag_agent.api.routes import chat
    chat_router = chat.router
    app.include_router(chat_router, prefix="/api/v1", tags=["chat"])
    logger.info("Chat routes loaded successfully")
except ImportError as e:
    logger.error(f"Could not import chat routes: {e}")
    logger.error("Chat routes will not be available. Please check your Python path configuration.")
    raise

if __name__ == "__main__":
    import uvicorn
    import sys
    import os
    # Add the backend directory to the Python path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    # This allows running the app directly for development
    uvicorn.run(
        "rag_agent.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )