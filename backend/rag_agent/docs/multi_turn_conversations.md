# Stateless Chat Architecture

## Overview
The RAG Agent Service uses a stateless architecture, where each chat request is processed independently without maintaining conversation history or session state between requests.

## Stateless Design

### Request Processing
- Each chat request is processed in isolation
- No persistent session state is maintained
- No need to track session IDs or conversation history
- Each request contains all necessary information for processing

### Request Flow
1. **User sends question**: Client sends a question to the `/api/v1/chat` endpoint
2. **Context retrieval**: System retrieves relevant context from Qdrant vector database based on the current question
3. **Response generation**: LLM generates response based only on current question and retrieved context
4. **Response returned**: Complete response is returned to the client

## Chat Flow

### Single Request
```bash
POST /api/v1/chat
{
  "question": "What is physical AI?"
}
```

The system processes the question independently and returns a response with relevant citations.

## Context Handling

### Context Retrieval
- Context is retrieved based solely on the current question
- No historical conversation context is used
- Each request is treated as a standalone query
- RAG pipeline retrieves relevant textbook content for each request

### Context Limitations
- No conversation history is maintained between requests
- Each question must be self-contained
- Follow-up questions need to provide sufficient context within the question itself

## API Endpoints

### Chat Endpoint
```
POST /api/v1/chat
```

Accepts a question and returns a response with citations. No session management required.

## Best Practices

### For Developers
- Design client applications to work with stateless requests
- No need to manage session IDs or conversation state
- Each request should be self-contained
- Handle responses independently

### For Users
- Each question should be self-contained with sufficient context
- No need to maintain or pass session information
- Responses are generated based on current question only

## Error Handling

Common scenarios:
- **No previous context**: Each request is independent, so no context is expected
- **Self-contained questions**: Ensure questions provide enough context to be understood independently

## Performance Considerations

- No session state to maintain in memory or database
- Each request is processed independently
- RAG retrieval happens for each request
- Optimized for single-question, single-response interactions

## Security

- No session state to secure
- No session ID management required
- Each request is processed independently
- No risk of session hijacking or session-related vulnerabilities