# Quickstart Guide: RAG Ingestion Pipeline

## Prerequisites
- Python 3.9+
- uv package manager
- Access to Cohere API
- Access to Qdrant Cloud

## Setup Instructions

1. **Clone the repository and navigate to backend directory**
   ```bash
   cd backend/
   ```

2. **Install dependencies using uv**
   ```bash
   uv pip install python-dotenv requests beautifulsoup4 cohere qdrant-client lxml
   ```

3. **Set up environment variables**
   Create a `.env` file with:
   ```
   COHERE_API_KEY=your_cohere_api_key_here
   QDRANT_URL=your_qdrant_cloud_url_here
   QDRANT_API_KEY=your_qdrant_api_key_here
   ```

4. **Run the ingestion pipeline**
   ```bash
   python main.py
   ```

## Expected Output
- All URLs from the Docusaurus site will be discovered
- Content will be extracted and chunked
- Embeddings will be generated and stored in Qdrant
- Validation will confirm successful ingestion