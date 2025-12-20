# Function Documentation: RAG Agent Service for Physical AI Textbook

## Module: agents/textbook_agent.py

### Class: TextbookAgent
The main AI agent that processes questions and generates responses based on textbook content.

#### Method: `__init__(self)`
Initializes the TextbookAgent with necessary services.

**Parameters:**
- None

**Returns:**
- Instance of TextbookAgent

**Side Effects:**
- Creates an OpenAI client instance
- Sets up retrieval tool reference
- Sets up conversation service reference

#### Method: `answer_question(self, question: str, session_id: Optional[str] = None, user_preferences: Optional[Dict[str, Any]] = None) -> ChatResponse`
Processes a user question and returns a response based on textbook content.

**Parameters:**
- `question` (str): The user's question about Physical AI concepts
- `session_id` (Optional[str]): Session identifier for conversation context
- `user_preferences` (Optional[Dict[str, Any]]): User preferences for response style

**Returns:**
- `ChatResponse`: The agent's response with citations and metadata

**Raises:**
- Various exceptions if processing fails

**Side Effects:**
- Updates conversation history if session_id is provided
- Logs processing metrics

#### Method: `_generate_answer_with_context(self, question: str, retrieved_contexts: List, user_preferences: Optional[Dict[str, Any]] = None, conversation_context: Optional[List[Dict[str, str]]] = None) -> str`
Generates an answer using retrieved context and conversation history.

**Parameters:**
- `question` (str): The original question
- `retrieved_contexts` (List): Contexts retrieved from the textbook
- `user_preferences` (Optional[Dict[str, Any]]): User preferences for response style
- `conversation_context` (Optional[List[Dict[str, str]]]): Previous conversation turns

**Returns:**
- `str`: The generated answer

#### Method: `_format_context_for_llm(self, retrieved_contexts: List) -> str`
Formats retrieved contexts for input to the LLM.

**Parameters:**
- `retrieved_contexts` (List): Retrieved contexts to format

**Returns:**
- `str`: Formatted context string

#### Method: `_build_prompt(self, question: str, context: str, conversation_history: str = "", detail_level: str = "intermediate", response_format: str = "detailed") -> str`
Builds the prompt for the LLM based on user preferences and context.

**Parameters:**
- `question` (str): The user's question
- `context` (str): Retrieved context content
- `conversation_history` (str): Previous conversation turns
- `detail_level` (str): Desired detail level
- `response_format` (str): Desired response format

**Returns:**
- `str`: The constructed prompt

#### Method: `_extract_citations(self, retrieved_contexts: List) -> List[Citation]`
Extracts citations from retrieved contexts.

**Parameters:**
- `retrieved_contexts` (List): Retrieved contexts to extract citations from

**Returns:**
- `List[Citation]`: List of extracted citations

#### Method: `validate_answer_grounding(self, question: str, answer: str, retrieved_contexts: List) -> bool`
Validates that the answer is grounded in the retrieved context.

**Parameters:**
- `question` (str): Original question
- `answer` (str): Generated answer
- `retrieved_contexts` (List): Retrieved contexts used

**Returns:**
- `bool`: Whether the answer is properly grounded

## Module: services/conversation.py

### Class: ConversationService
Manages conversation sessions and history.

#### Method: `__init__(self)`
Initializes the ConversationService.

**Parameters:**
- None

**Returns:**
- Instance of ConversationService

#### Method: `create_session(self, user_id: Optional[str] = None, metadata: Optional[Dict] = None) -> ConversationSession`
Creates a new conversation session.

**Parameters:**
- `user_id` (Optional[str]): User identifier
- `metadata` (Optional[Dict]): Additional session metadata

**Returns:**
- `ConversationSession`: The created session

#### Method: `get_session(self, session_id: str) -> Optional[ConversationSession]`
Retrieves an existing session.

**Parameters:**
- `session_id` (str): Session identifier

**Returns:**
- `Optional[ConversationSession]`: The session if found, None otherwise

#### Method: `update_session(self, session_id: str, new_data: Dict[str, Any]) -> bool`
Updates an existing session.

**Parameters:**
- `session_id` (str): Session identifier
- `new_data` (Dict[str, Any]): Data to update

**Returns:**
- `bool`: Whether update was successful

#### Method: `add_conversation_turn(self, session_id: str, question: str, response: str) -> bool`
Adds a question-response pair to the conversation history.

**Parameters:**
- `session_id` (str): Session identifier
- `question` (str): The question asked
- `response` (str): The response given

**Returns:**
- `bool`: Whether addition was successful

#### Method: `get_conversation_context(self, session_id: str, max_turns: int = 5) -> List[Dict[str, str]]`
Gets recent conversation context for follow-up questions.

**Parameters:**
- `session_id` (str): Session identifier
- `max_turns` (int): Maximum number of turns to retrieve

**Returns:**
- `List[Dict[str, str]]`: Recent conversation turns

#### Method: `end_session(self, session_id: str) -> bool`
Ends and removes a conversation session.

**Parameters:**
- `session_id` (str): Session identifier

**Returns:**
- `bool`: Whether ending was successful

#### Method: `cleanup_expired_sessions(self)`
Removes sessions that have exceeded the timeout.

**Parameters:**
- None

**Returns:**
- None

**Side Effects:**
- Removes expired sessions from memory

## Module: services/validation.py

### Class: ResponseValidationService
Validates agent responses and citations.

#### Method: `validate_response_citations(self, response: ChatResponse, retrieved_contexts: Optional[List[RetrievedContext]] = None) -> Dict[str, Any]`
Validates that the response includes proper source citations.

**Parameters:**
- `response` (ChatResponse): The response to validate
- `retrieved_contexts` (Optional[List[RetrievedContext]]): Contexts used to generate response

**Returns:**
- `Dict[str, Any]`: Validation results

#### Method: `validate_citation_quality(self, citations: List[Citation], min_confidence_score: float = 0.5) -> Dict[str, Any]`
Validates the quality of citations based on confidence scores.

**Parameters:**
- `citations` (List[Citation]): Citations to validate
- `min_confidence_score` (float): Minimum acceptable confidence score

**Returns:**
- `Dict[str, Any]`: Quality validation results

#### Method: `validate_response_completeness(self, response: ChatResponse) -> Dict[str, Any]`
Validates the overall completeness and quality of the response.

**Parameters:**
- `response` (ChatResponse): The response to validate

**Returns:**
- `Dict[str, Any]`: Completeness validation results

## Module: agents/retrieval_tool.py

### Class: QdrantRetrievalTool
Connects to Qdrant to retrieve textbook content.

#### Method: `__init__(self)`
Initializes the retrieval tool with Qdrant client.

**Parameters:**
- None

**Returns:**
- Instance of QdrantRetrievalTool

#### Method: `retrieve_context(self, query: str, top_k: Optional[int] = None) -> List[RetrievedContext]`
Retrieves context from Qdrant based on the query.

**Parameters:**
- `query` (str): The query to search for
- `top_k` (Optional[int]): Number of results to return

**Returns:**
- `List[RetrievedContext]`: Retrieved context chunks

#### Method: `_get_embedding(self, text: str) -> List[float]`
Gets embedding for the input text using an external service.

**Parameters:**
- `text` (str): Text to embed

**Returns:**
- `List[float]`: Embedding vector

#### Method: `_search_qdrant(self, query_embedding: List[float], top_k: int) -> List`
Performs vector similarity search in Qdrant.

**Parameters:**
- `query_embedding` (List[float]): Query embedding vector
- `top_k` (int): Number of results to return

**Returns:**
- `List`: Search results

#### Method: `validate_retrieval(self, query: str, expected_chunks: List[str] = None) -> Dict[str, Any]`
Validates retrieval quality for the given query.

**Parameters:**
- `query` (str): Query to validate
- `expected_chunks` (List[str]): Expected result IDs

**Returns:**
- `Dict[str, Any]`: Validation results

## Module: services/agent_service.py

### Class: AgentService
Main service that orchestrates all components of the RAG Agent.

#### Method: `__init__(self)`
Initializes the agent service with all required components.

**Parameters:**
- None

**Returns:**
- Instance of AgentService

#### Method: `process_request(self, chat_request: ChatRequest) -> ChatResponse`
Process a chat request through all service components with error handling and fallbacks.

**Parameters:**
- `chat_request` (ChatRequest): The incoming chat request

**Returns:**
- `ChatResponse`: The processed response

#### Method: `process_request_with_circuit_breaker(self, chat_request: ChatRequest, max_retries: int = 2) -> ChatResponse`
Process a request with circuit breaker pattern and retry logic.

**Parameters:**
- `chat_request` (ChatRequest): The incoming chat request
- `max_retries` (int): Maximum number of retry attempts

**Returns:**
- `ChatResponse`: The processed response

#### Method: `process_request_with_detailed_logging(self, chat_request: ChatRequest) -> Dict[str, Any]`
Process a request with detailed performance and logging information.

**Parameters:**
- `chat_request` (ChatRequest): The incoming chat request

**Returns:**
- `Dict[str, Any]`: Processing log with detailed information

#### Method: `validate_service_health(self) -> Dict[str, Any]`
Validate the health of all service components.

**Parameters:**
- None

**Returns:**
- `Dict[str, Any]`: Health status of all components

#### Method: `get_service_metrics(self) -> Dict[str, Any]`
Get metrics about service usage and performance.

**Parameters:**
- None

**Returns:**
- `Dict[str, Any]`: Service metrics

## Module: api/routes/chat.py

### Router: `router`
FastAPI router for chat endpoints.

#### Endpoint: `POST /chat`
Submit a question to the RAG agent.

**Request Body:**
- `ChatRequest`: Question and preferences

**Response:**
- `ChatResponse`: Answer with citations

#### Endpoint: `POST /session`
Create a new conversation session.

**Response:**
- `SessionResponse`: New session information

#### Endpoint: `GET /session/{session_id}`
Get session information.

**Parameters:**
- `session_id` (str): Session identifier

**Response:**
- `Dict[str, Any]`: Session information

#### Endpoint: `DELETE /session/{session_id}`
End a conversation session.

**Parameters:**
- `session_id` (str): Session identifier

**Response:**
- `Dict[str, str]`: Confirmation message

## Module: utils/helpers.py

### Function: `timer()`
Context manager for timing code execution.

**Usage:**
```python
with timer():
    # code to time
```

### Function: `time_it(func: Callable) -> Callable`
Decorator to time function execution.

**Parameters:**
- `func` (Callable): Function to time

**Returns:**
- `Callable`: Timed function

### Function: `time_it_async(func: Callable) -> Callable`
Async decorator to time async function execution.

**Parameters:**
- `func` (Callable): Async function to time

**Returns:**
- `Callable`: Timed async function

### Function: `calculate_similarity_score(text1: str, text2: str) -> float`
Calculate a basic similarity score between two texts (0.0 to 1.0).

**Parameters:**
- `text1` (str): First text
- `text2` (str): Second text

**Returns:**
- `float`: Similarity score between 0.0 and 1.0

### Function: `format_timestamp(timestamp: Optional[datetime] = None) -> str`
Format a datetime object as an ISO string.

**Parameters:**
- `timestamp` (Optional[datetime]): Timestamp to format, defaults to current time

**Returns:**
- `str`: Formatted timestamp

## Module: utils/logger.py

### Function: `setup_logger(name: str, level: Optional[str] = None) -> logging.Logger`
Set up a logger with the specified name and level.

**Parameters:**
- `name` (str): Logger name
- `level` (Optional[str]): Logging level

**Returns:**
- `logging.Logger`: Configured logger

### Function: `get_logger(name: str) -> logging.Logger`
Get a logger instance with the specified name.

**Parameters:**
- `name` (str): Logger name

**Returns:**
- `logging.Logger`: Logger instance

## Module: config/settings.py

### Class: Settings
Application settings loaded from environment variables.

**Attributes:**
- `openai_api_key` (str): OpenAI API key
- `qdrant_url` (str): Qdrant service URL
- `qdrant_api_key` (str): Qdrant API key
- `qdrant_collection_name` (str): Name of the collection to query
- `log_level` (str): Logging level
- `default_top_k` (int): Default number of results to retrieve
- `session_timeout_minutes` (int): Minutes of inactivity before session expires
- `agent_model` (str): OpenAI model to use
- `max_response_tokens` (int): Maximum response tokens
- `temperature` (float): Response generation temperature
- `max_concurrent_requests` (int): Maximum concurrent requests
- `response_timeout_seconds` (int): Response timeout in seconds
- `api_version` (str): API version
- `api_prefix` (str): API prefix
- `allowed_origins` (List[str]): Allowed origins for CORS

## Module: main.py

### Variable: `app`
FastAPI application instance.

### Function: `lifespan(app: FastAPI) -> AsyncIterator[None]`
Application lifespan manager for startup and shutdown events.

**Parameters:**
- `app` (FastAPI): FastAPI application instance

**Yields:**
- None

**Side Effects:**
- Logs startup and shutdown events