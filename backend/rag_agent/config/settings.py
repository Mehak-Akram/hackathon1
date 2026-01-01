"""
Configuration settings for the RAG Agent Service using Pydantic BaseSettings
"""
from pydantic_settings import BaseSettings
from typing import Optional, List
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    # API Configuration
    # Support both OpenAI and OpenRouter APIs
    openrouter_api_key: Optional[str] = Field(default=None, description="OpenRouter API key for agent functionality", alias="OPENROUTER_API_KEY")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key for agent functionality", alias="OPENAI_API_KEY")
    qdrant_url: str = Field(..., description="URL for the Qdrant retrieval service", alias="QDRANT_URL")
    qdrant_api_key: str = Field(..., description="API key for Qdrant access", alias="QDRANT_API_KEY")
    qdrant_collection_name: str = Field(default="ragchtbot_embadding", description="Name of the collection to query", alias="QDRANT_COLLECTION_NAME")
    cohere_api_key: Optional[str] = Field(default=None, description="Cohere API key (if needed)", alias="COHERE_API_KEY")

    # Database Configuration
    neon_database_url: Optional[str] = Field(default=None, description="Neon Postgres database URL", alias="NEON_DATABASE_URL")

    # Application Configuration
    log_level: str = Field(default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR)", alias="LOG_LEVEL")
    default_top_k: int = Field(default=5, description="Default number of results to retrieve", alias="DEFAULT_TOP_K")

    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Host for the server to bind to", alias="HOST")
    port: int = Field(default=8000, description="Port for the server to listen on", alias="PORT")

    # Agent Configuration
    agent_model: str = Field(default="openai/gpt-4o", description="Default model to use")
    max_response_tokens: int = Field(default=1000, description="Maximum number of tokens in agent responses")
    temperature: float = Field(default=0.1, ge=0.0, le=1.0, description="Temperature for response generation (lower = more factual)")

    # Performance Configuration
    max_concurrent_requests: int = Field(default=100, description="Maximum number of concurrent requests to handle")
    response_timeout_seconds: int = Field(default=30, description="Timeout for API responses in seconds")

    # API Endpoint Configuration
    api_version: str = Field(default="v1", description="API version for endpoints")
    api_prefix: str = Field(default="/api", description="API prefix for all endpoints")
    allowed_origins: List[str] = Field(default=["*"], description="List of allowed origins for CORS")

    class Config:
        env_file = ".env"
        case_sensitive = True
        populate_by_name = True  # Allow both alias and field name


# Create a singleton instance of settings
settings = Settings()