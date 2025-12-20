# RAG Retrieval Pipeline for Physical AI Textbook

This pipeline implements semantic search functionality against Qdrant Cloud using Cohere-generated embeddings to support downstream AI agents. It retrieves top-k relevant content chunks with complete metadata for RAG applications.

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   # Or if using pyproject.toml:
   pip install .
   ```

2. **Configure environment variables**:
   Copy the `.env` file and set your API keys:
   ```bash
   cp .env .env.local
   # Edit .env.local and add your keys:
   # COHERE_API_KEY=your_cohere_api_key_here
   # QDRANT_URL=your_qdrant_cloud_url_here
   # QDRANT_API_KEY=your_qdrant_api_key_here
   ```

## Usage

### Basic Retrieval
```python
from retrieval_pipeline import retrieve_content

# Retrieve top-3 most relevant chunks for a query
results = retrieve_content("What are neural networks?", top_k=3)

for chunk in results:
    print(f"Score: {chunk.similarity_score}")
    print(f"Content: {chunk.content[:200]}...")
    print(f"Source: {chunk.chapter} - {chunk.section}")
    print()
```

### Agent-Ready Formatting
```python
from retrieval_pipeline import retrieve_content, format_for_agent

# Retrieve content
results = retrieve_content("How do machine learning algorithms work?")

# Format for agent consumption
agent_ready = format_for_agent(results)
print(f"Formatted {len(agent_ready)} chunks for agent consumption")
```

### Validation Testing
```python
from retrieval_pipeline import validate_retrieval, ValidationQuery

# Create validation queries
validation_queries = [
    ValidationQuery(
        query_text="What are neural networks?",
        expected_chunks=["expected-chunk-id-1", "expected-chunk-id-2"],
        query_category="definition"
    )
]

# Run validation
results = validate_retrieval(validation_queries)

for result in results:
    print(f"Accuracy: {result.accuracy_score:.3f}")
    print(f"Precision: {result.precision:.3f}")
    print(f"Recall: {result.recall:.3f}")
```

## Configuration

The pipeline can be configured using environment variables in your `.env` file:

- `QDRANT_COLLECTION_NAME`: The Qdrant collection to search (default: ragchtbot_embadding)
- `DEFAULT_TOP_K`: Default number of results to retrieve (default: 5)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

## Architecture

The pipeline follows this flow:
```
[Query] → [Embedding Generation] → [Vector Similarity Search] → [Results with Metadata] → [Validation]
```

1. **Query Processing**: Natural language queries are converted to embeddings using Cohere
2. **Vector Search**: Embeddings are used to find similar content in Qdrant
3. **Result Formatting**: Retrieved chunks include complete metadata for attribution
4. **Validation**: Quality metrics ensure accurate retrieval

## Testing

Run the test suite to verify functionality:
```bash
cd backend/retrieval_pipeline
python test_retrieval.py
```

## Performance

The pipeline is optimized for sub-second retrieval latency with 95th percentile performance under 1 second for local execution. Results are deterministic, returning consistent results for identical queries.

## Compatibility

This pipeline is designed to work with content ingested using the RAG ingestion pipeline (Spec-1), using the same Cohere embedding model (multilingual-v3.0) and Qdrant collection schema for compatibility.