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
    session_id: Optional[str] = Field(
        default=None,
        description="Existing session identifier (creates new if not provided)"
    )
    user_preferences: Optional[UserPreferences] = Field(
        default=None,
        description="User preferences for response style and detail level"
    )

    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not cls._is_valid_uuid(v):
            raise ValueError('session_id must be a valid UUID')
        return v

    @staticmethod
    def _is_valid_uuid(uuid_string: str) -> bool:
        try:
            uuid.UUID(uuid_string)
            return True
        except ValueError:
            return False

    @field_validator('question')
    @classmethod
    def validate_question(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Question cannot be empty or whitespace only')
        return v.strip()


class SessionRequest(BaseModel):
    """
    Model for session creation requests
    """
    user_id: Optional[str] = Field(
        default=None,
        description="Identifier for the user (if authenticated)"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional session metadata"
    )

    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not cls._is_valid_uuid(v):
            raise ValueError('user_id must be a valid UUID')
        return v

    @staticmethod
    def _is_valid_uuid(uuid_string: str) -> bool:
        try:
            uuid.UUID(uuid_string)
            return True
        except ValueError:
            return False


class Question(BaseModel):
    """
    Model for a natural language query from the end user seeking information about Physical AI concepts
    """
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for the question"
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="The actual question text from the user"
    )
    session_id: str = Field(
        ...,
        description="Reference to the conversation session"
    )
    timestamp: str = Field(
        default_factory=lambda: __import__('datetime').datetime.now(__import__('pytz').timezone('UTC')).isoformat(),
        description="When the question was submitted"
    )
    user_id: Optional[str] = Field(
        default=None,
        description="Identifier for the user (if authenticated)"
    )

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Content cannot be empty or whitespace only')
        if len(v) > 1000:
            raise ValueError('Content must be 1-1000 characters')
        return v.strip()

    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        if not cls._is_valid_uuid(v):
            raise ValueError('session_id must be a valid UUID')
        return v

    @field_validator('user_id')
    @classmethod
    def validate_user_id_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not cls._is_valid_uuid(v):
            raise ValueError('user_id must be a valid UUID')
        return v

    @staticmethod
    def _is_valid_uuid(uuid_string: str) -> bool:
        try:
            uuid.UUID(uuid_string)
            return True
        except ValueError:
            return False


class ConversationSession(BaseModel):
    """
    Model for a sequence of related questions and answers that maintains context for follow-up queries
    """
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for the session"
    )
    created_at: str = Field(
        default_factory=lambda: __import__('datetime').datetime.now(__import__('pytz').timezone('UTC')).isoformat(),
        description="When the session was created"
    )
    last_activity: str = Field(
        default_factory=lambda: __import__('datetime').datetime.now(__import__('pytz').timezone('UTC')).isoformat(),
        description="When the last interaction occurred"
    )
    user_id: Optional[str] = Field(
        default=None,
        description="Identifier for the user (if authenticated)"
    )
    conversation_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="History of question-response pairs",
        max_length=50
    )
    active: bool = Field(
        default=True,
        description="Whether the session is currently active"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional session metadata"
    )

    @field_validator('conversation_history')
    @classmethod
    def validate_conversation_history(cls, v: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if len(v) > 50:
            raise ValueError('Conversation history must not exceed 50 question-response pairs')
        return v

    @field_validator('id', 'user_id')
    @classmethod
    def validate_uuid_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not cls._is_valid_uuid(v):
            raise ValueError('Must be a valid UUID')
        return v

    @staticmethod
    def _is_valid_uuid(uuid_string: str) -> bool:
        try:
            uuid.UUID(uuid_string)
            return True
        except ValueError:
            return False