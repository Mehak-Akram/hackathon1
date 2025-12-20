# RAG Agent Service for Physical AI Textbook

## Overview

The RAG (Retrieval-Augmented Generation) Agent Service provides an AI-powered interface for querying a Physical AI textbook using natural language. The service retrieves relevant content from a Qdrant vector database and generates accurate, textbook-grounded responses with proper source citations.

## Features

- **Natural Language Queries**: Ask questions about Physical AI concepts in plain English
- **Grounded Responses**: Answers are based solely on textbook content with no hallucination
- **Source Citations**: Each response includes citations to specific textbook sections
- **Conversation Context**: Maintains session state for follow-up questions
- **User Preferences**: Customize response detail level and format
- **Performance Optimized**: Sub-10 second response times for 95% of queries
- **Production Ready**: Robust error handling, monitoring, and scalability

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │────│   RAG Agent      │────│  Qdrant Vector  │
│   Application   │    │   Service        │    │   Database      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                       ┌──────────────────┐
                       │   OpenAI API     │
                       └──────────────────┘
```

### Components
- **API Layer**: FastAPI endpoints for chat and session management
- **Agent Service**: Core orchestration of all components
- **Textbook Agent**: AI agent for question answering
- **Retrieval Tool**: Interface to Qdrant vector database
- **Conversation Service**: Session and context management
- **Validation Service**: Response quality and grounding checks

## Prerequisites

- Python 3.11+
- OpenAI API access
- Qdrant vector database access
- Git (for cloning the repository)

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd <repository-directory>
```

### 2. Set up Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root with the following variables:

```env
# API Configuration
OPENAI_API_KEY=your_openai_api_key_here
QDRANT_URL=your_qdrant_url_here
QDRANT_API_KEY=your_qdrant_api_key_here
QDRANT_COLLECTION_NAME=your_collection_name

# Application Configuration
LOG_LEVEL=INFO
DEFAULT_TOP_K=5
SESSION_TIMEOUT_MINUTES=30

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

## Usage

### 1. Start the Service
```bash
cd backend/rag_agent
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The service will be available at `http://localhost:8000`

### 2. Submit a Question
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the fundamental principles of physical AI?",
    "user_preferences": {
      "detail_level": "intermediate",
      "response_format": "detailed"
    }
  }'
```

### 3. Create a Session for Multi-turn Conversations
```bash
curl -X POST http://localhost:8000/api/v1/session \
  -H "Content-Type: application/json" \
  -d '{}'
```

### 4. Use Session ID for Follow-up Questions
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How does this apply to robotics?",
    "session_id": "your-session-id-from-previous-request",
    "user_preferences": {
      "detail_level": "intermediate",
      "response_format": "detailed"
    }
  }'
```

## API Endpoints

### Chat Endpoint
```
POST /api/v1/chat
```
Submit a question to the RAG agent.

### Session Management
```
POST /api/v1/session          # Create new session
GET /api/v1/session/{id}      # Get session info
DELETE /api/v1/session/{id}   # End session
```

### Health Check
```
GET /
GET /health
```

## Configuration

### Environment Variables
- `OPENAI_API_KEY`: OpenAI API key for agent functionality
- `QDRANT_URL`: URL for the Qdrant retrieval service
- `QDRANT_API_KEY`: API key for Qdrant access
- `QDRANT_COLLECTION_NAME`: Name of the collection to query
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `DEFAULT_TOP_K`: Default number of results to retrieve (default: 5)
- `SESSION_TIMEOUT_MINUTES`: Minutes of inactivity before session expires (default: 30)
- `AGENT_MODEL`: OpenAI model to use (default: gpt-4-turbo-preview)
- `TEMPERATURE`: Response randomness (default: 0.1 for factual responses)

### User Preferences
The API supports user preferences for:
- `detail_level`: "basic", "intermediate", or "advanced"
- `response_format`: "concise", "detailed", or "examples"

## Performance

- **Response Time**: <10 seconds for 95% of requests
- **Throughput**: Supports 100+ concurrent user sessions
- **Availability**: 99% uptime target
- **Scalability**: Horizontal scaling with load balancer support

## Testing

### Run Unit Tests
```bash
cd backend/rag_agent
python -m pytest tests/unit/ -v
```

### Run Integration Tests
```bash
cd backend/rag_agent
python -m pytest tests/integration/ -v
```

### Run All Tests
```bash
cd backend/rag_agent
python -m pytest tests/ -v
```

## Development

### Project Structure
```
backend/rag_agent/
├── main.py                 # FastAPI application entry point
├── agents/
│   ├── textbook_agent.py   # Core AI agent implementation
│   └── retrieval_tool.py   # Tool for integrating with retrieval pipeline
├── api/
│   ├── routes/
│   │   └── chat.py         # Chat endpoint routes
│   └── models/
│       ├── request.py      # Request models (Question, Session)
│       └── response.py     # Response models (AgentResponse, Citation)
├── services/
│   ├── conversation.py     # Conversation context management
│   └── validation.py       # Response validation service
├── config/
│   └── settings.py         # Configuration and settings
├── utils/
│   └── helpers.py          # Utility functions
├── docs/
│   ├── ...
└── tests/
    ├── unit/
    ├── integration/
    └── contract/
```

## Deployment

### Production Deployment
For production deployment, consider:

1. **Environment Setup**:
   - Use a production WSGI server (e.g., Gunicorn)
   - Set appropriate resource limits
   - Configure SSL/TLS termination

2. **Monitoring**:
   - Set up application monitoring
   - Configure logging aggregation
   - Set up performance alerts

3. **Security**:
   - Implement API authentication
   - Set up rate limiting
   - Validate and sanitize inputs

### Example Production Command
```bash
gunicorn main:app --workers 4 --bind 0.0.0.0:8000 --timeout 300
```

## Troubleshooting

### Common Issues

1. **API Key Errors**: Verify that all required API keys are properly set in the environment
2. **Retrieval Pipeline Unavailable**: Check that the Qdrant URL and credentials are correct
3. **Response Timeouts**: Increase timeout settings if dealing with complex queries
4. **Session Loss**: Check session timeout configuration and client implementation

### Logging
The service logs to stdout with configurable log levels. Check logs for detailed error information.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite (`python -m pytest tests/`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the repository or contact the development team.

---

Built with ❤️ for the Physical AI community.