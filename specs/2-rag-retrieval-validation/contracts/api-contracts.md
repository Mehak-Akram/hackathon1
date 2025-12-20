# API Contracts: RAG Retrieval & Validation Pipeline

## Core Functions Interface

### retrieve_content(query: str, top_k: int = 5) -> List[RetrievedChunk]
- **Purpose**: Perform semantic search and retrieve top-k relevant content chunks
- **Input**: Natural language query string and number of results to return
- **Output**: List of RetrievedChunk objects with content and metadata
- **Errors**: API errors, network errors, validation errors

### get_embedding(text: str) -> List[float]
- **Purpose**: Generate embedding vector for input text using Cohere
- **Input**: Text string to convert to embedding
- **Output**: 1024-dimensional embedding vector
- **Errors**: API errors, rate limits, validation errors

### validate_embedding_dimensions(vector: List[float]) -> bool
- **Purpose**: Validate that embedding vector has correct dimensions
- **Input**: Embedding vector to validate
- **Output**: Boolean indicating if dimensions are correct
- **Errors**: None (validation only)

### validate_retrieval(queries: List[ValidationQuery]) -> ValidationResult
- **Purpose**: Validate retrieval quality against known queries
- **Input**: List of validation queries with expected results
- **Output**: Comprehensive validation results with accuracy metrics
- **Errors**: Validation errors, processing errors

### search_qdrant(query_embedding: List[float], top_k: int = 5) -> List[RetrievedChunk]
- **Purpose**: Perform vector similarity search in Qdrant
- **Input**: Query embedding vector and number of results to return
- **Output**: List of RetrievedChunk objects from Qdrant
- **Errors**: Database errors, connection errors, query errors

### format_for_agent(chunks: List[RetrievedChunk]) -> List[Dict]
- **Purpose**: Format retrieved chunks for agent-ready consumption
- **Input**: List of RetrievedChunk objects
- **Output**: List of dictionaries formatted for agent consumption
- **Errors**: Formatting errors, validation errors