# OpenRouter AI Agent

This project integrates OpenRouter with OpenAI Agent SDK by configuring AsyncOpenAI client to use OpenRouter's API endpoint. The system loads OPENROUTER_API_KEY from environment variables using python-dotenv and configures the agent to use google/gemini-2.0-flash model while ensuring compatibility with Agent, Runner, and RunConfig components.

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
5. Add your OPENROUTER_API_KEY to the .env file

## Docker Deployment

The project includes a Dockerfile for containerized deployment:

1. Build the Docker image:
   ```bash
   docker build -t rag-agent .
   ```

2. Run the container:
   ```bash
   docker run -p 8000:8000 --env-file .env rag-agent
   ```

## Hugging Face Spaces Deployment

To deploy on Hugging Face Spaces:

1. Add the Dockerfile to your repository
2. Create a Space with Docker SDK
3. Push your code to the repository
4. The Space will automatically build and deploy your application

Make sure to add your environment variables in the Space settings.

## Usage

TODO: Add usage instructions after implementation