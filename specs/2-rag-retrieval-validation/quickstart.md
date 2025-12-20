# Quickstart Guide: RAG Retrieval & Validation Pipeline

## Prerequisites
- Python 3.9+
- Access to Cohere API
- Access to Qdrant Cloud (with the collection from Spec-1: "ragchtbot_embadding")
- API keys for both services

## Setup Instructions

1. **Clone the repository and navigate to backend directory**
   ```bash
   cd backend/
   ```

2. **Install dependencies**
   ```bash
   pip install qdrant-client cohere python-dotenv pydantic fastapi uvicorn
   ```

3. **Set up environment variables**
   Create a `.env` file with:
   ```
   COHERE_API_KEY=your_cohere_api_key_here
   QDRANT_URL=your_qdrant_cloud_url_here
   QDRANT_API_KEY=your_qdrant_api_key_here
   ```

4. **Run the retrieval pipeline**
   ```bash
   python -c "from retrieval_pipeline import retrieve_content; result = retrieve_content('your query here'); print(result)"
   ```

## Expected Output
- Query is converted to embedding using Cohere
- Semantic search is performed against Qdrant
- Top-k relevant chunks with metadata are returned
- Each result includes clean text, source URL, chapter, section, and similarity score