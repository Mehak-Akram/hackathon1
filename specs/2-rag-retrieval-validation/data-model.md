# Data Model: RAG Retrieval & Validation Pipeline

## Entities

### Query
- **text**: string (the natural language query from user/agent)
- **embedding**: List[float] (1024-dimensional vector representation)
- **top_k**: integer (number of results to retrieve, default 5)

### RetrievedChunk
- **content**: string (the actual text content of the chunk)
- **chunk_id**: string (unique identifier for the chunk in Qdrant)
- **url**: string (source URL of the content)
- **chapter**: string (chapter name/identifier from hierarchy)
- **section**: string (section name within chapter)
- **heading_hierarchy**: List[string] (hierarchy of headings from the document)
- **similarity_score**: float (cosine similarity score between query and chunk)
- **metadata**: Dict (additional metadata as key-value pairs)

### ValidationQuery
- **query_text**: string (the input query text)
- **expected_chunks**: List[string] (expected chunk IDs or content for validation)
- **query_category**: string (category of query for testing, e.g., "definition", "concept", "example")

### ValidationResult
- **query_id**: string (identifier for the test query)
- **retrieved_chunks**: List[RetrievedChunk] (chunks returned by the system)
- **expected_chunks**: List[string] (chunks that should have been returned)
- **accuracy_score**: float (measured accuracy for this query)
- **precision**: float (precision metric)
- **recall**: float (recall metric)
- **is_correct**: boolean (whether retrieval was considered correct)
- **execution_time**: float (time taken for retrieval in seconds)

### QdrantSearchResult
- **points**: List[RetrievedChunk] (retrieved points from Qdrant)
- **search_params**: Dict (parameters used for the search)
- **total_points_found**: integer (total number of points found before top-k filtering)
- **execution_time**: float (time taken for the search operation)