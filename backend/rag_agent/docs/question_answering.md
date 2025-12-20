# Question Answering Functionality

## Overview
The RAG Agent Service provides a question answering capability that allows users to ask questions about Physical AI concepts and receive answers grounded in textbook content with proper source attribution.

## How It Works

### 1. Query Processing
- User submits a natural language question via the `/api/v1/chat` endpoint
- The system validates the input and creates/uses a session ID for context tracking

### 2. Context Retrieval
- The retrieval tool connects to the Qdrant vector database
- Uses embeddings to find semantically similar content from the Physical AI textbook
- Returns top-k most relevant content chunks based on similarity scores

### 3. Answer Generation
- The textbook agent formats the retrieved context for the LLM
- Uses OpenAI's API to generate a response based only on the provided context
- Applies user preferences for detail level and response format

### 4. Response Validation
- Validates that the generated answer is grounded in the retrieved content
- Ensures no hallucination of information outside the textbook
- Adds proper source citations to the response

## API Usage

### Chat Endpoint
```
POST /api/v1/chat
```

**Request Body:**
```json
{
  "question": "What are the fundamental principles of physical AI?",
  "session_id": "optional-session-id",
  "user_preferences": {
    "detail_level": "intermediate",
    "response_format": "detailed"
  }
}
```

**Response:**
```json
{
  "response": "Physical AI combines robotics, machine learning, and physics...",
  "session_id": "session-id",
  "citations": [
    {
      "source_url": "https://textbook.example.com/chapter3/section2",
      "chapter": "Chapter 3: Physical AI Fundamentals",
      "section": "3.2 Principles of Physical Interaction",
      "similarity_score": 0.87
    }
  ],
  "retrieved_context_count": 3,
  "response_time": 4.25
}
```

## User Preferences

### Detail Level Options:
- `basic`: Simple, straightforward answers
- `intermediate`: Moderately detailed with key points
- `advanced`: Comprehensive, technical answers

### Response Format Options:
- `concise`: Brief and to the point
- `detailed`: Thorough explanations
- `examples`: Includes relevant examples

## Session Management

### Create Session
```
POST /api/v1/session
```

### Session Endpoint
```
GET /api/v1/session/{session_id}
DELETE /api/v1/session/{session_id}
```

Sessions automatically timeout after 30 minutes of inactivity (configurable).

## Configuration

The system behavior can be configured via environment variables in `.env`:
- `DEFAULT_TOP_K`: Number of context chunks to retrieve (default: 5)
- `SESSION_TIMEOUT_MINUTES`: Session timeout duration (default: 30)
- `AGENT_MODEL`: OpenAI model to use (default: gpt-4-turbo-preview)
- `TEMPERATURE`: Response randomness (default: 0.1 for factual responses)

## Validation and Quality Assurance

- All responses are validated to ensure they're grounded in retrieved content
- Source citations are provided for all information
- Response time is measured and reported
- Error handling ensures graceful degradation

## Error Handling

Common error responses:
- `400`: Invalid request (malformed question, invalid session ID)
- `404`: Session not found
- `500`: Internal server error or API service unavailable

## Performance

- Target response time: <10 seconds for 95% of requests
- Supports 100+ concurrent sessions
- Configurable timeout settings