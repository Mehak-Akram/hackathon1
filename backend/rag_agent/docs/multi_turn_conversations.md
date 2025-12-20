# Multi-Turn Conversations and Session Management

## Overview
The RAG Agent Service supports multi-turn conversations, allowing users to ask follow-up questions and maintain context throughout their interaction with the textbook assistant.

## Session Management

### Session Lifecycle
1. **Creation**: Sessions are created either explicitly via the `/session` endpoint or implicitly when a question is asked without a session ID
2. **Active Period**: Sessions remain active for 30 minutes of inactivity (configurable via `SESSION_TIMEOUT_MINUTES`)
3. **Expiration**: Expired sessions are automatically cleaned up
4. **Termination**: Sessions can be explicitly ended via the `/session/{session_id}` DELETE endpoint

### Session Structure
Each session maintains:
- Unique session ID (UUID)
- User ID (optional)
- Creation and last activity timestamps
- Conversation history (limited to 50 most recent turns)
- Session metadata
- Active status

## Multi-Turn Conversation Flow

### Starting a Conversation
```bash
POST /api/v1/chat
{
  "question": "What is physical AI?"
}
```

The system will automatically create a new session and return the session ID in the response.

### Continuing a Conversation
```bash
POST /api/v1/chat
{
  "question": "How does it differ from traditional AI?",
  "session_id": "abc123-uuid-from-previous-response"
}
```

The system will retrieve the conversation history and use it as context for answering the follow-up question.

### Explicit Session Creation
```bash
POST /api/v1/session
{
  "user_id": "optional-user-identifier",
  "metadata": {
    "user_type": "student",
    "course": "Physical AI 101"
  }
}
```

## Conversation Context Handling

### Context Inclusion
The system includes up to 5 most recent conversation turns when processing follow-up questions:
- Previous questions and answers are formatted and provided to the LLM
- The LLM uses this context to understand references and maintain conversation flow
- Context is only included when a valid session ID is provided

### Context Limitations
- Conversation history is limited to 50 turns to prevent memory issues
- Only the 5 most recent turns are included in the LLM prompt for performance
- Historical context is preserved in the session but older turns are not sent to the LLM

## API Endpoints

### Chat Endpoint with Session
```
POST /api/v1/chat
```

Includes session ID in request to maintain conversation context.

### Session Management Endpoints
```
POST /api/v1/session          # Create a new session
GET /api/v1/session/{id}      # Get session information
DELETE /api/v1/session/{id}   # End a session
```

## Configuration

Session behavior can be configured via environment variables:
- `SESSION_TIMEOUT_MINUTES`: Duration before session expires (default: 30)
- `MAX_CONCURRENT_SESSIONS`: Maximum number of concurrent sessions (coming soon)
- `CONVERSATION_HISTORY_TURNS`: Number of turns to include in context (default: 5)

## Best Practices

### For Developers
- Always handle the session ID returned from chat responses
- Implement session ID persistence in your client application
- Handle session expiration gracefully
- Consider implementing client-side session timeouts

### For Users
- Include the session ID in follow-up questions to maintain context
- Sessions are automatically cleaned up after 30 minutes of inactivity
- Long conversations may have older context truncated from the LLM prompt

## Error Handling

Common scenarios:
- **Invalid session ID**: Treated as a new session
- **Expired session**: Treated as a new session
- **Session limit reached**: Older conversations are automatically pruned

## Performance Considerations

- Conversation history is stored in memory (use Redis in production)
- Context formatting happens on each request
- Large conversation histories may impact response times
- The system is optimized for short to medium-length conversations

## Security

- Session IDs are UUIDs to prevent guessing
- No sensitive user information is stored in sessions by default
- Session cleanup prevents memory leaks
- Implement authentication if needed for your use case