# Gemini AI Agent

This project integrates Google Gemini (free tier) with OpenAI Agent SDK by configuring AsyncOpenAI client to use Gemini's OpenAI-compatible endpoint. The system loads GEMINI_API_KEY from environment variables using python-dotenv and configures the agent to use gemini-2.0-flash model while ensuring compatibility with Agent, Runner, and RunConfig components.

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
5. Add your GEMINI_API_KEY to the .env file

## Usage

TODO: Add usage instructions after implementation