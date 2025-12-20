# API Contracts: Chatbot UI Component for Docusaurus

## Overview
This document defines the API contracts for the chatbot UI component that integrates with the Docusaurus-based Physical AI textbook.

## Base URL
`http://localhost:8000/api/v1` (or production equivalent)

## 1. Chat API

### 1.1 Send Question (Enhanced)
**Endpoint**: `POST /chat`
**Description**: Send a question to the RAG agent with additional UI context

**Request**:
```json
{
  "question": "string (required) - The user's question",
  "session_id": "string (optional) - Session identifier for conversation context",
  "user_preferences": {
    "detail_level": "string (optional) - 'basic', 'intermediate', or 'advanced'",
    "response_format": "string (optional) - 'concise', 'detailed', or 'examples'",
    "include_citations": "boolean (optional) - Whether to include source citations"
  },
  "page_context": {
    "url": "string (required) - URL of the current page",
    "title": "string (required) - Title of the current page",
    "selectedText": "string (optional) - Text currently selected by the user",
    "pageTitle": "string (required) - Title of the document/page",
    "pageContent": "string (optional) - Relevant content from the current page (truncated)"
  }
}
```

**Response (Success)**:
```json
{
  "response": "string (required) - The agent's response to the question",
  "session_id": "string (required) - The session identifier",
  "citations": [
    {
      "id": "string (required) - Unique identifier for the citation",
      "source_url": "string (required) - URL of the source content",
      "chapter": "string (required) - Chapter name/identifier",
      "section": "string (required) - Section name within chapter",
      "heading": "string (optional) - Specific heading within the section",
      "page_reference": "string (optional) - Page number or location reference",
      "similarity_score": "number (optional) - How relevant this source was to the response",
      "text_excerpt": "string (optional) - Excerpt of the text that was used",
      "source_type": "string (optional) - Type of source",
      "confidence_score": "number (optional) - Confidence in the accuracy of this citation"
    }
  ],
  "retrieved_context_count": "number (required) - Number of context chunks used",
  "response_time": "number (required) - Time taken to generate the response in seconds",
  "followup_suggestions": "array[string] (optional) - Suggested follow-up questions"
}
```

**Response Codes**:
- `200 OK`: Question processed successfully
- `400 Bad Request`: Invalid request format or missing required fields
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error during processing

### 1.2 Get Session Info
**Endpoint**: `GET /session/{session_id}`
**Description**: Get information about a specific chat session

**Response (Success)**:
```json
{
  "session_id": "string (required) - The session identifier",
  "active": "boolean (required) - Whether the session is currently active",
  "created_at": "string (required) - When the session was created (ISO 8601)",
  "last_activity": "string (required) - When the last interaction occurred (ISO 8601)",
  "user_id": "string (optional) - Identifier for the user (if authenticated)",
  "conversation_count": "number (required) - Number of conversation turns in the session",
  "metadata": "object (optional) - Additional session metadata"
}
```

**Response Codes**:
- `200 OK`: Session information retrieved successfully
- `400 Bad Request`: Invalid session ID format
- `404 Not Found`: Session not found

### 1.3 Create New Session
**Endpoint**: `POST /session`
**Description**: Create a new conversation session

**Request**:
```json
{
  "user_id": "string (optional) - User identifier if authenticated",
  "metadata": "object (optional) - Additional session metadata"
}
```

**Response (Success)**:
```json
{
  "session_id": "string (required) - The new session identifier",
  "created_at": "string (required) - When the session was created (ISO 8601)"
}
```

**Response Codes**:
- `200 OK`: Session created successfully
- `400 Bad Request`: Invalid request format

## 2. Frontend Component API

### 2.1 Initialize Chat Component
**Description**: The frontend component should be initialized with these props

**Props Interface**:
```typescript
interface ChatComponentProps {
  backendUrl: string; // Base URL for the backend API
  initialSessionId?: string; // Optional existing session ID
  pageContext?: {
    url: string; // Current page URL
    title: string; // Current page title
    content?: string; // Current page content (truncated)
  };
  userPreferences?: {
    detailLevel?: 'basic' | 'intermediate' | 'advanced';
    responseFormat?: 'concise' | 'detailed' | 'examples';
    includeCitations?: boolean;
  };
  onSessionChange?: (sessionId: string) => void; // Callback when session ID changes
  onMessageReceived?: (message: ChatMessage) => void; // Callback when message is received
  className?: string; // Additional CSS classes
  style?: React.CSSProperties; // Additional inline styles
}
```

### 2.2 Component Events
The component should emit these events:

- `onSessionCreated(sessionId: string)`: When a new session is created
- `onMessageSent(message: string)`: When user sends a message
- `onMessageReceived(response: ChatResponse)`: When response is received from backend
- `onError(error: Error)`: When an error occurs
- `onSessionCleared()`: When session is cleared by user

## 3. Data Models (Frontend)

### 3.1 ChatMessage
```typescript
interface ChatMessage {
  id: string; // Unique identifier
  role: 'user' | 'assistant'; // Message sender
  content: string; // Message content
  timestamp: string; // ISO 8601 timestamp
  sources?: SourceReference[]; // Source citations for assistant messages
  isLoading?: boolean; // Whether message is still loading (for assistant)
}
```

### 3.2 SourceReference
```typescript
interface SourceReference {
  id: string; // Unique identifier
  source_url: string; // URL of the source
  chapter: string; // Chapter name
  section: string; // Section name
  heading?: string; // Specific heading
  page_reference?: string; // Page reference
  similarity_score?: number; // Relevance score (0.0-1.0)
  text_excerpt?: string; // Excerpt text
  source_type?: string; // Source type
  confidence_score?: number; // Confidence score (0.0-1.0)
}
```

## 4. Error Handling

### 4.1 Backend Error Response Format
```json
{
  "error": "string (required) - Error code",
  "message": "string (required) - Human-readable error message",
  "details": "object (optional) - Additional error details"
}
```

### 4.2 Common Error Codes
- `AGENT_ERROR`: General agent processing error
- `RETRIEVAL_ERROR`: Error during content retrieval
- `VALIDATION_ERROR`: Request validation failed
- `SESSION_ERROR`: Session-related error
- `RATE_LIMIT_EXCEEDED`: Rate limit exceeded

## 5. Security Considerations

### 5.1 Input Validation
- All string inputs should be validated for length and content
- URLs should be validated using proper URL validation
- Session IDs should be validated as proper UUIDs

### 5.2 Rate Limiting
- Implement rate limiting at 10 requests per minute per IP
- Consider implementing user-based rate limiting when authentication is available

### 5.3 Content Security
- Sanitize all content before rendering to prevent XSS
- Validate and sanitize source URLs before creating links
- Implement proper CORS policies for frontend integration