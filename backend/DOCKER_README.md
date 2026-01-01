# Docker Deployment for Hugging Face Spaces

This directory contains the Docker configuration for deploying the RAG Agent Service on Hugging Face Spaces.

## Dockerfile Overview

The Dockerfile is configured to:

- Use Python 3.11 slim image for a minimal footprint
- Install system dependencies (gcc, g++)
- Install Python requirements from requirements.txt
- Copy the entire backend application
- Expose port 8000
- Run the FastAPI application using uvicorn

## Environment Variables

Create a `.env` file in the root of your repository with the following environment variables:

```
OPENROUTER_API_KEY=your_openrouter_api_key
COHERE_API_KEY=your_cohere_api_key
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_api_key
DOCUSAURUS_BASE_URL=https://hackathon1-7k7o.vercel.app/
```

## Hugging Face Spaces Configuration

To deploy on Hugging Face Spaces:

1. Create a new Space with the following settings:
   - SDK: Docker
   - Hardware: Choose appropriate hardware based on your needs (CPU or GPU)
   - Enable "Allow Creds" if you need to handle authentication

2. Push your code with the Dockerfile to the repository

3. The Space will automatically build and deploy your application

## Alternative: Using Docker Compose (Optional)

If you prefer to use Docker Compose for local testing, create a `docker-compose.yml` file:

```yaml
version: '3.8'
services:
  rag-agent:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      - HOST=0.0.0.0
      - PORT=8000
```

## Health Check Endpoints

The application provides the following health check endpoints:
- `GET /health` - Basic health check
- `GET /api/v1/health` - Detailed health check
- `GET /api/v1/health/service` - Service component health check

## Notes for Hugging Face Deployment

- Make sure your application listens on port 8000
- The application should handle the `PORT` environment variable if provided by Hugging Face
- Consider adding a startup script to handle any initialization tasks
- The Docker image will be built automatically when you push to Hugging Face Spaces