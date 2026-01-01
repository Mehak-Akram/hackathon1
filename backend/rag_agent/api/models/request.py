"""
Request models for the RAG Agent Service API
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from enum import Enum
import uuid


class DetailLevel(str, Enum):
    """
    Enum for detail level preferences
    """
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ResponseFormat(str, Enum):
    """
    Enum for response format preferences
    """
    CONCISE = "concise"
    DETAILED = "detailed"
    EXAMPLES = "examples"


class UserPreferences(BaseModel):
    """
    Model for user preferences in requests
    """
    detail_level: Optional[DetailLevel] = Field(
        default=DetailLevel.INTERMEDIATE,
        description="Desired level of technical detail"
    )
    response_format: Optional[ResponseFormat] = Field(
        default=ResponseFormat.DETAILED,
        description="Preferred response format"
    )


class ChatRequest(BaseModel):
    """
    Model for chat requests to the RAG agent
    """
    question: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="The user's question about Physical AI concepts"
    )
    user_preferences: Optional[UserPreferences] = Field(
        default=None,
        description="User preferences for response style and detail level"
    )

    @field_validator('question')
    @classmethod
    def validate_question(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Question cannot be empty or whitespace only')
        return v.strip()


class CreateUserRequest(BaseModel):
    """
    Model for creating a new user
    """
    email: str = Field(
        ...,
        min_length=5,
        max_length=255,
        description="User's email address"
    )
    username: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=50,
        description="Optional username"
    )
    full_name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Optional full name"
    )


class CreateChatMessageRequest(BaseModel):
    """
    Model for creating a new chat message
    """
    role: str = Field(
        ...,
        pattern=r"^(user|assistant|system)$",
        description="Role of the message sender"
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Content of the message"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata for the message"
    )


