"""
Response models for the RAG Agent Service API
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


class Citation(BaseModel):
    """
    Model for references to specific textbook sections, chapters, or pages that were used to generate the response
    """
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for the citation"
    )
    source_url: str = Field(
        ...,
        description="URL of the source content"
    )
    chapter: str = Field(
        ...,
        description="Chapter name/identifier"
    )
    section: str = Field(
        ...,
        description="Section name within chapter"
    )
    heading: Optional[str] = Field(
        default=None,
        description="Specific heading within the section"
    )
    page_reference: Optional[str] = Field(
        default=None,
        description="Page number or location reference"
    )
    similarity_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="How relevant this source was to the response (0.0 to 1.0)"
    )
    text_excerpt: Optional[str] = Field(
        default=None,
        description="Excerpt of the text that was used to generate the response"
    )
    source_type: Optional[str] = Field(
        default="textbook",
        description="Type of source (e.g., textbook, paper, article)"
    )
    confidence_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence in the accuracy of this citation (0.0 to 1.0)"
    )
    citation_date: Optional[str] = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Date when this citation was created/used"
    )

    @field_validator('source_url')
    @classmethod
    def validate_source_url(cls, v: str) -> str:
        if not cls._is_valid_url(v):
            raise ValueError('source_url must be a valid URL')
        return v

    @staticmethod
    def _is_valid_url(url: str) -> bool:
        import re
        regex = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url is not None and regex.search(url) is not None


class RetrievedContext(BaseModel):
    """
    Model for textbook content chunks retrieved based on semantic similarity to the user's question
    """
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for the context chunk"
    )
    content: str = Field(
        ...,
        description="The actual content text from the textbook"
    )
    url: str = Field(
        ...,
        description="Source URL of the content"
    )
    chapter: str = Field(
        ...,
        description="Chapter name/identifier from hierarchy"
    )
    section: str = Field(
        ...,
        description="Section name within chapter"
    )
    heading_hierarchy: List[str] = Field(
        ...,
        description="Hierarchy of headings from the document"
    )
    similarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Cosine similarity score between query and chunk"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata as key-value pairs"
    )

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Content must not be empty')
        return v

    @field_validator('similarity_score')
    @classmethod
    def validate_similarity_score(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError('Similarity score must be between 0.0 and 1.0')
        return v

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not cls._is_valid_url(v):
            raise ValueError('URL must be a valid URL format')
        return v

    @field_validator('chapter', 'section')
    @classmethod
    def validate_required_fields(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Chapter and section must not be empty')
        return v.strip()

    @staticmethod
    def _is_valid_url(url: str) -> bool:
        import re
        regex = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url is not None and regex.search(url) is not None


class AgentResponse(BaseModel):
    """
    Model for the AI-generated answer that combines retrieved context with natural language processing, including source citations
    """
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for the response"
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="The actual response text from the agent"
    )
    session_id: str = Field(
        ...,
        description="Reference to the conversation session"
    )
    question_id: str = Field(
        ...,
        description="Reference to the original question"
    )
    retrieved_contexts: List[RetrievedContext] = Field(
        default_factory=list,
        description="List of contexts used to generate the response"
    )
    citations: List[Citation] = Field(
        default_factory=list,
        description="List of source citations"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="When the response was generated"
    )
    response_time: float = Field(
        ...,
        gt=0,
        description="Time taken to generate the response in seconds"
    )

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Content must not be empty or whitespace only')
        if len(v) > 10000:
            raise ValueError('Content must be 1-10000 characters')
        return v.strip()

    @field_validator('session_id', 'question_id')
    @classmethod
    def validate_ids(cls, v: str) -> str:
        if not cls._is_valid_uuid(v):
            raise ValueError('Must be a valid UUID')
        return v

    @staticmethod
    def _is_valid_uuid(uuid_string: str) -> bool:
        try:
            import uuid
            import uuid
            uuid.UUID(uuid_string)
            return True
        except ValueError:
            return False

    @field_validator('retrieved_contexts')
    @classmethod
    def validate_retrieved_contexts(cls, v: List[RetrievedContext]) -> List[RetrievedContext]:
        # For error responses, an empty list might be acceptable
        # But in most cases, we expect some context to be used
        return v

    @field_validator('response_time')
    @classmethod
    def validate_response_time(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('Response time must be positive')
        return v

    @staticmethod
    def _is_valid_uuid(uuid_string: str) -> bool:
        try:
            import uuid
            uuid.UUID(uuid_string)
            return True
        except ValueError:
            return False


class ChatResponse(BaseModel):
    """
    Model for API response to chat interactions
    """
    response: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="The agent's response to the question"
    )
    session_id: str = Field(
        ...,
        description="The session identifier"
    )
    citations: List[Citation] = Field(
        ...,
        description="List of source citations used in the response"
    )
    retrieved_context_count: int = Field(
        ...,
        ge=0,
        description="Number of context chunks used to generate the response"
    )
    response_time: float = Field(
        ...,
        gt=0,
        description="Time taken to generate the response in seconds"
    )
    followup_suggestions: Optional[List[str]] = Field(
        default=None,
        description="Suggested follow-up questions"
    )

    @field_validator('response')
    @classmethod
    def validate_response(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Response must not be empty or whitespace only')
        if len(v) > 10000:
            raise ValueError('Response must be 1-10000 characters')
        return v.strip()

    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        if not cls._is_valid_uuid(v):
            raise ValueError('Session ID must be a valid UUID')
        return v

    @field_validator('citations')
    @classmethod
    def validate_citations(cls, v: List[Citation]) -> List[Citation]:
        # Validate that citations list matches the citations in the agent response
        # This will be checked during response generation
        return v

    @field_validator('response_time')
    @classmethod
    def validate_response_time(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('Response time must be positive')
        return v

    @staticmethod
    def _is_valid_uuid(uuid_string: str) -> bool:
        try:
            import uuid
            uuid.UUID(uuid_string)
            return True
        except ValueError:
            return False


class SessionResponse(BaseModel):
    """
    Model for API response to session creation
    """
    session_id: str = Field(
        ...,
        description="The new session identifier"
    )
    created_at: str = Field(
        ...,
        description="When the session was created"
    )

    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        if not cls._is_valid_uuid(v):
            raise ValueError('Session ID must be a valid UUID')
        return v

    @staticmethod
    def _is_valid_uuid(uuid_string: str) -> bool:
        try:
            import uuid
            uuid.UUID(uuid_string)
            return True
        except ValueError:
            return False


class ErrorResponse(BaseModel):
    """
    Model for API error responses
    """
    error: str = Field(
        ...,
        description="Error code"
    )
    message: str = Field(
        ...,
        description="Human-readable error message"
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details"
    )