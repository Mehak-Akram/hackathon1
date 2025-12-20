# Quickstart: Gemini AI Agent Integration

## Prerequisites

- Python 3.9 or higher
- Google Cloud account with Gemini API access
- GEMINI_API_KEY from Google Cloud Console

## Setup

### 1. Clone the repository
```bash
git clone <repository-url>
cd <repository-name>
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
Create a `.env` file in the project root:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

## Usage

### Initialize the Gemini Agent
```python
from backend.src.agents.gemini_agent import GeminiAgent

# Initialize the agent
agent = GeminiAgent()

# Run a simple query
response = await agent.run("Hello, how are you?")
print(response)
```

### Using the AsyncOpenAI Client Directly
```python
from backend.src.agents.agent_config import create_gemini_client

client = create_gemini_client()

# Make a direct call
response = await client.chat.completions.create(
    model="gemini-2.0-flash",
    messages=[{"role": "user", "content": "Hello, world!"}]
)

print(response.choices[0].message.content)
```

## Configuration

The agent is configured automatically by loading the GEMINI_API_KEY from environment variables using python-dotenv. The base_url is set to Gemini's OpenAI-compatible endpoint by default.

## Testing

Run the unit tests:
```bash
pytest tests/unit/
```

Run the integration tests:
```bash
pytest tests/integration/
```

## Troubleshooting

### API Key Issues
- Ensure GEMINI_API_KEY is properly set in your environment
- Verify the API key has access to the Gemini API
- Check that you're using the correct endpoint URL

### Connection Issues
- Verify network connectivity to https://generativelanguage.googleapis.com
- Check that the base_url is correctly configured as https://generativelanguage.googleapis.com/v1beta/openai/