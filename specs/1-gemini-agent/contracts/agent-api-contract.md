# API Contract: Gemini Agent Integration

## Overview
This document defines the API contract for the Gemini AI Agent that integrates with OpenAI Agent SDK but connects to Google Gemini's OpenAI-compatible endpoint.

## Base URL
```
https://generativelanguage.googleapis.com/v1beta/openai/
```

## Authentication
Authentication is handled via the `Authorization` header with Bearer token:
```
Authorization: Bearer {GEMINI_API_KEY}
```

## API Endpoints

### Chat Completions
**Endpoint**: `POST /chat/completions`

**Description**: Creates a completion for the chat message using the Gemini model

**Request**:
```json
{
  "model": "gemini-2.0-flash",
  "messages": [
    {
      "role": "user",
      "content": "Hello, how are you?"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 150
}
```

**Response**:
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "gemini-2.0-flash",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "I'm doing well, thank you for asking!"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 9,
    "completion_tokens": 12,
    "total_tokens": 21
  }
}
```

### Agent Run Endpoint
**Endpoint**: `POST /agent/run`

**Description**: Runs the AI agent with the provided input

**Request**:
```json
{
  "input": "What is the capital of France?",
  "config": {
    "model": "gemini-2.0-flash",
    "temperature": 0.7
  }
}
```

**Response**:
```json
{
  "output": "The capital of France is Paris.",
  "metadata": {
    "model_used": "gemini-2.0-flash",
    "response_time": 0.5
  }
}
```

## Error Responses

All error responses follow the standard format:
```json
{
  "error": {
    "type": "invalid_request_error",
    "message": "The model parameter is required",
    "code": "model_required"
  }
}
```

## Supported Models
- `gemini-2.0-flash` - Free tier model for quick responses

## Rate Limits
- Subject to Google Cloud API quotas and limits
- Check Google Cloud Console for specific limits based on your project