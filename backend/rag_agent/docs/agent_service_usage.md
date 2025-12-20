# RAG Agent Service Usage and Validation Procedures

## Overview
This document provides comprehensive information about using the RAG Agent Service for Physical AI Textbook, including setup, usage patterns, and validation procedures.

## Service Architecture

### Components
The RAG Agent Service consists of several key components:
- **Textbook Agent**: Core AI agent that processes questions and generates responses
- **Retrieval Tool**: Connects to Qdrant vector database to retrieve relevant textbook content
- **Conversation Service**: Manages session state and conversation history
- **Validation Service**: Ensures responses are grounded in retrieved content and properly cited
- **Agent Service**: Orchestrates all components and handles request processing

### Data Flow
1. User submits a question via the API
2. The Agent Service processes the request, maintaining conversation context
3. The Retrieval Tool queries Qdrant for relevant textbook content
4. The Textbook Agent generates a response based on retrieved context
5. The Validation Service ensures response grounding and citation accuracy
6. Response is returned to the user with proper citations

## API Usage

### Base URL
```
https://your-domain.com/api/v1
```

### Endpoints

#### Chat Endpoint
```
POST /chat
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
      "id": "unique-id",
      "source_url": "https://textbook.example.com/chapter1",
      "chapter": "Chapter 1: Introduction",
      "section": "1.1 Overview",
      "similarity_score": 0.85,
      "text_excerpt": "Physical AI combines robotics, machine learning, and physics...",
      "confidence_score": 0.85
    }
  ],
  "retrieved_context_count": 3,
  "response_time": 4.25
}
```

#### Session Management
```
POST /session
GET /session/{session_id}
DELETE /session/{session_id}
```

### User Preferences

#### Detail Level Options
- `basic`: Simple, straightforward answers
- `intermediate`: Moderately detailed with key points
- `advanced`: Comprehensive, technical answers with details

#### Response Format Options
- `concise`: Keep the response brief and to the point
- `detailed`: Provide a thorough explanation with examples where appropriate
- `examples`: Include relevant examples from the context

## Configuration

### Environment Variables
```env
# API Configuration
OPENAI_API_KEY=your_openai_api_key
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_api_key
QDRANT_COLLECTION_NAME=your_collection_name

# Application Configuration
LOG_LEVEL=INFO
DEFAULT_TOP_K=5
SESSION_TIMEOUT_MINUTES=30

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

### Performance Tuning
- `DEFAULT_TOP_K`: Number of context chunks to retrieve (default: 5)
- `SESSION_TIMEOUT_MINUTES`: Session timeout duration (default: 30)
- `AGENT_MODEL`: OpenAI model to use (default: gpt-4-turbo-preview)
- `TEMPERATURE`: Response randomness (default: 0.1 for factual responses)

## Validation Procedures

### Response Quality Validation
The system validates responses through multiple checks:

#### Content Grounding
- Ensures responses are based only on retrieved textbook content
- Verifies that no information outside the provided context is included
- Measures semantic similarity between response and source content

#### Citation Accuracy
- Validates that all citations reference actual retrieved contexts
- Checks that citation fields are complete and properly formatted
- Ensures citation sources match the retrieved content

#### Performance Validation
- Monitors response time (target: <10 seconds for 95% of requests)
- Tracks system availability (target: 99% uptime)
- Measures concurrent session handling (target: 100+ sessions)

### Testing Procedures

#### Unit Tests
```bash
cd backend/rag_agent
python -m pytest tests/unit/ -v
```

#### Integration Tests
```bash
cd backend/rag_agent
python -m pytest tests/integration/ -v
```

#### Performance Tests
```bash
cd backend/rag_agent
python -m pytest tests/performance/ -v
```

### Validation Endpoints
The service provides health and metrics endpoints:
- `GET /health`: Basic service health check
- `GET /metrics`: Performance and usage metrics
- `GET /validation`: Validation status and quality metrics

## Error Handling and Fallbacks

### Common Error Types
- **Retrieval Error**: Unable to find relevant content in the textbook
- **Agent Error**: Issue with the AI agent processing
- **Validation Error**: Response doesn't meet quality standards

### Fallback Mechanisms
- Automatic retry with exponential backoff
- Simplified processing when conversation context unavailable
- Graceful degradation when external services are slow

## Monitoring and Logging

### Log Levels
- `DEBUG`: Detailed diagnostic information
- `INFO`: General operational information
- `WARNING`: Potential issues that don't affect operation
- `ERROR`: Errors that affect operation

### Key Metrics
- Response time percentiles (50th, 95th, 99th)
- Request success rate
- Citation accuracy rate
- Session persistence success rate

## Security Considerations

### Authentication
- API keys for external service access
- Rate limiting to prevent abuse
- Input validation to prevent injection attacks

### Data Privacy
- No personal data storage by default
- Session data retention limited to timeout period
- Encrypted transmission for all API communications

## Deployment

### Requirements
- Python 3.11+
- OpenAI API access
- Qdrant vector database access
- 2GB+ RAM for optimal performance

### Startup
```bash
cd backend/rag_agent
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Scaling
- Horizontal scaling with load balancer
- Session affinity for conversation continuity
- Database connection pooling for external services

## Troubleshooting

### Common Issues
1. **Slow Response Times**: Check Qdrant connectivity and OpenAI API status
2. **No Citations**: Verify Qdrant collection has content and proper indexing
3. **Session Loss**: Check session timeout configuration and client implementation

### Diagnostic Commands
```bash
# Check service health
curl http://localhost:8000/health

# Test basic functionality
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is physical AI?"}'
```

## Performance Optimization

### Response Time Optimization
- Cache frequently requested content
- Optimize vector search parameters
- Implement response caching for identical questions

### Resource Management
- Connection pooling for external services
- Memory management for conversation history
- Cleanup of expired sessions

## Best Practices

### For Developers
- Always handle session IDs for conversation continuity
- Implement proper error handling and fallbacks
- Monitor response times and citation accuracy
- Test with diverse question types

### For Users
- Formulate specific questions for better retrieval
- Use session IDs to maintain context across requests
- Provide feedback on response quality when possible
- Respect rate limits and usage guidelines

## Quality Assurance

### Continuous Validation
- Automated testing for response quality
- Regular validation of citation accuracy
- Performance monitoring and alerting
- Periodic review of grounding effectiveness

### Metrics Dashboard
The system provides real-time metrics on:
- Response quality scores
- Citation accuracy rates
- System performance indicators
- User satisfaction metrics (when available)

This documentation serves as a comprehensive guide for deploying, using, and maintaining the RAG Agent Service for Physical AI Textbook.