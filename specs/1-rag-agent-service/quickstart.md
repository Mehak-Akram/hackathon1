# Quickstart Guide: RAG Agent Service for Physical AI Textbook

## Overview
This guide provides instructions for setting up and running the RAG Agent Service that answers questions about Physical AI concepts using textbook content.

## Prerequisites
- Python 3.11 or higher
- pip package manager
- Access to OpenAI API (API key)
- Access to Qdrant retrieval pipeline (URL and API key)

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
OPENAI_API_KEY=your_openai_api_key_here
QDRANT_URL=your_qdrant_url_here
QDRANT_API_KEY=your_qdrant_api_key_here
QDRANT_COLLECTION_NAME=your_collection_name
LOG_LEVEL=INFO
DEFAULT_TOP_K=5
SESSION_TIMEOUT_MINUTES=30
```

## Running the Service

### 1. Start the API Server
```bash
cd backend/rag_agent
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

### 2. Verify the Service
Check that the service is running:
```bash
curl http://localhost:8000/health
```

## API Usage

### Submit a Question
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-token" \
  -d '{
    "question": "What are the fundamental principles of physical AI?",
    "user_preferences": {
      "detail_level": "intermediate",
      "response_format": "detailed"
    }
  }'
```

### Create a New Session
```bash
curl -X POST http://localhost:8000/api/v1/chat/session \
  -H "Authorization: Bearer your-api-token"
```

## Configuration Options

### Environment Variables
- `OPENAI_API_KEY`: OpenAI API key for agent functionality
- `QDRANT_URL`: URL for the Qdrant retrieval service
- `QDRANT_API_KEY`: API key for Qdrant access
- `QDRANT_COLLECTION_NAME`: Name of the collection to query
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `DEFAULT_TOP_K`: Default number of results to retrieve (default: 5)
- `SESSION_TIMEOUT_MINUTES`: Minutes of inactivity before session expires (default: 30)

### Response Customization
The API supports user preferences for:
- `detail_level`: "basic", "intermediate", or "advanced"
- `response_format`: "concise", "detailed", or "examples"

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

### Run Contract Tests
```bash
cd backend/rag_agent
python -m pytest tests/contract/ -v
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
│       ├── request.py      # Request models
│       └── response.py     # Response models
├── services/
│   ├── conversation.py     # Conversation context management
│   └── validation.py       # Response validation service
└── config/
    └── settings.py         # Configuration and settings
```

## Troubleshooting

### Common Issues
1. **API Key Errors**: Verify that all required API keys are properly set in the environment
2. **Retrieval Pipeline Unavailable**: Check that the Qdrant URL and credentials are correct
3. **Response Timeouts**: Increase timeout settings if dealing with complex queries

### Logging
The service logs to stdout with configurable log levels. Check logs for detailed error information.

## Next Steps
1. Integrate the API into your frontend application
2. Implement user authentication if required
3. Set up monitoring and alerting for production deployments
4. Add the chatbot UI component to your Docusaurus site as described in the sections above
5. Customize the chatbot component to match your textbook's styling and requirements