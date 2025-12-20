# Data Model: RAG Agent Service for Physical AI Textbook

## Entity: Question
**Description**: A natural language query from the end user seeking information about Physical AI concepts

**Fields**:
- `id`: String (UUID) - Unique identifier for the question
- `content`: String (required) - The actual question text from the user
- `session_id`: String (required) - Reference to the conversation session
- `timestamp`: DateTime (required) - When the question was submitted
- `user_id`: String (optional) - Identifier for the user (if authenticated)

**Validation Rules**:
- Content must be 1-1000 characters
- Content must not be empty or whitespace only
- Session_id must be a valid UUID format

---

## Entity: RetrievedContext
**Description**: Textbook content chunks retrieved based on semantic similarity to the user's question

**Fields**:
- `id`: String (UUID) - Unique identifier for the context chunk
- `content`: String (required) - The actual content text from the textbook
- `url`: String (required) - Source URL of the content
- `chapter`: String (required) - Chapter name/identifier from hierarchy
- `section`: String (required) - Section name within chapter
- `heading_hierarchy`: List[String] (required) - Hierarchy of headings from the document
- `similarity_score`: Float (required) - Cosine similarity score between query and chunk
- `metadata`: Dict (optional) - Additional metadata as key-value pairs

**Validation Rules**:
- Content must not be empty
- Similarity score must be between 0.0 and 1.0
- URL must be a valid URL format
- Chapter and section must not be empty

---

## Entity: AgentResponse
**Description**: The AI-generated answer that combines retrieved context with natural language processing, including source citations

**Fields**:
- `id`: String (UUID) - Unique identifier for the response
- `content`: String (required) - The actual response text from the agent
- `session_id`: String (required) - Reference to the conversation session
- `question_id`: String (required) - Reference to the original question
- `retrieved_contexts`: List[RetrievedContext] (required) - List of contexts used to generate the response
- `citations`: List[Citation] (required) - List of source citations
- `timestamp`: DateTime (required) - When the response was generated
- `response_time`: Float (required) - Time taken to generate the response in seconds

**Validation Rules**:
- Content must be 1-10000 characters
- Content must not be empty or whitespace only
- Retrieved contexts list must not be empty (except for error responses)
- Citations must correspond to the retrieved contexts used

---

## Entity: Citation
**Description**: References to specific textbook sections, chapters, or pages that were used to generate the response

**Fields**:
- `id`: String (UUID) - Unique identifier for the citation
- `source_url`: String (required) - URL of the source content
- `chapter`: String (required) - Chapter name/identifier
- `section`: String (required) - Section name within chapter
- `heading`: String (optional) - Specific heading within the section
- `page_reference`: String (optional) - Page number or location reference
- `similarity_score`: Float (optional) - How relevant this source was to the response

**Validation Rules**:
- Source URL must be a valid URL format
- Chapter and section must not be empty
- Similarity score must be between 0.0 and 1.0 if provided

---

## Entity: ConversationSession
**Description**: A sequence of related questions and answers that maintains context for follow-up queries

**Fields**:
- `id`: String (UUID) - Unique identifier for the session
- `created_at`: DateTime (required) - When the session was created
- `last_activity`: DateTime (required) - When the last interaction occurred
- `user_id`: String (optional) - Identifier for the user (if authenticated)
- `conversation_history`: List[Dict] (required) - History of question-response pairs
- `active`: Boolean (required) - Whether the session is currently active
- `metadata`: Dict (optional) - Additional session metadata

**Validation Rules**:
- Conversation history must not exceed 50 question-response pairs
- Session must be marked inactive after 30 minutes of inactivity
- Active must be a boolean value

---

## Entity: ChatRequest
**Description**: API request model for chat interactions

**Fields**:
- `question`: String (required) - The user's question
- `session_id`: String (optional) - Existing session identifier (creates new if not provided)
- `user_preferences`: Dict (optional) - User preferences for response style, detail level, etc.

**Validation Rules**:
- Question must be 1-1000 characters
- Question must not be empty or whitespace only
- Session_id must be a valid UUID format if provided

---

## Entity: ChatResponse
**Description**: API response model for chat interactions

**Fields**:
- `response`: String (required) - The agent's response to the question
- `session_id`: String (required) - The session identifier
- `citations`: List[Citation] (required) - List of source citations used in the response
- `retrieved_context_count`: Integer (required) - Number of context chunks used
- `response_time`: Float (required) - Time taken to generate the response in seconds
- `followup_suggestions`: List[String] (optional) - Suggested follow-up questions

**Validation Rules**:
- Response must be 1-10000 characters
- Citations list must match the citations in the agent response
- Response time must be positive

---

## Entity: ChatMessage
**Description**: Represents a single message in the chat conversation

**Fields**:
- `id`: String (UUID, required) - Unique identifier for the message
- `role`: String (required) - Either "user" or "assistant"
- `content`: String (required) - The text content of the message
- `timestamp`: DateTime (required) - When the message was created
- `sources`: List[SourceReference] (optional) - Source citations for assistant responses
- `isLoading`: Boolean (optional) - Whether the message is still being processed

**Validation Rules**:
- `id` must be a valid UUID
- `role` must be either "user" or "assistant"
- `content` must not be empty
- `timestamp` must be in ISO 8601 format

---

## Entity: SourceReference
**Description**: Reference to a specific source in the textbook used in an assistant response

**Fields**:
- `id`: String (UUID, required) - Unique identifier for the source reference
- `source_url`: String (required) - URL of the source content
- `chapter`: String (required) - Chapter name/identifier
- `section`: String (required) - Section name within chapter
- `heading`: String (optional) - Specific heading within the section
- `page_reference`: String (optional) - Page number or location reference
- `similarity_score`: Float (optional) - How relevant this source was to the response (0.0 to 1.0)
- `text_excerpt`: String (optional) - Excerpt of the text that was used
- `source_type`: String (optional) - Type of source (default: "textbook")
- `confidence_score`: Float (optional) - Confidence in the accuracy of this citation (0.0 to 1.0)

**Validation Rules**:
- `source_url` must be a valid URL format
- `similarity_score` must be between 0.0 and 1.0
- `confidence_score` must be between 0.0 and 1.0

---

## Entity: ChatSession
**Description**: Represents a conversation session with message history

**Fields**:
- `id`: String (UUID, required) - Unique identifier for the session
- `messages`: List[ChatMessage] (required) - Array of messages in the conversation
- `createdAt`: DateTime (required) - When the session was created
- `lastActive`: DateTime (required) - When the last message was added
- `pageContext`: PageContext (optional) - Context of the page where the chat was initiated
- `isActive`: Boolean (optional) - Whether the session is currently active

**Validation Rules**:
- `id` must be a valid UUID
- `messages` must not exceed 100 messages (to prevent memory issues)
- `createdAt` and `lastActive` must be in ISO 8601 format

---

## Entity: PageContext
**Description**: Context information about the page where the chat is embedded

**Fields**:
- `url`: String (required) - URL of the current page
- `title`: String (required) - Title of the current page
- `selectedText`: String (optional) - Text currently selected by the user
- `pageTitle`: String (required) - Title of the document/page
- `pageContent`: String (optional) - Relevant content from the current page (truncated)
- `documentMetadata`: Dict (optional) - Additional metadata about the document

**Validation Rules**:
- `url` must be a valid URL format
- `selectedText` must not exceed 1000 characters to prevent large payloads

---

## Entity: ChatRequestFrontend
**Description**: Request payload from the frontend with additional UI context

**Fields**:
- `question`: String (required) - The user's question
- `session_id`: String (optional) - Session identifier for conversation context
- `user_preferences`: UserPreferences (optional) - User preferences for response style
- `page_context`: PageContext (optional) - Context about the current page
- `selected_text`: String (optional) - Text selected by the user

**Validation Rules**:
- `question` must not be empty
- `session_id` must be a valid UUID if provided
- `question` must not exceed 2000 characters

---

## Entity: UserPreferences
**Description**: User preferences that influence the response style

**Fields**:
- `detail_level`: String (optional) - "basic", "intermediate", or "advanced" (default: "intermediate")
- `response_format`: String (optional) - "concise", "detailed", or "examples" (default: "detailed")
- `include_citations`: Boolean (optional) - Whether to include source citations (default: true)

**Validation Rules**:
- `detail_level` must be one of the allowed values
- `response_format` must be one of the allowed values