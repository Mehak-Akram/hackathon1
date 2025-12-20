# API Contracts: RAG Ingestion Pipeline

## Functions Interface

### get_all_urls(base_url: str) -> List[str]
- **Purpose**: Discover all content URLs from a Docusaurus site
- **Input**: Base URL of the Docusaurus site
- **Output**: List of all discovered content URLs
- **Errors**: Network errors, parsing errors

### extract_text_from_url(url: str) -> str
- **Purpose**: Extract clean text content from a webpage
- **Input**: URL to extract content from
- **Output**: Clean text content
- **Errors**: Network errors, parsing errors

### chunk_text(text: str, url: str = "") -> List[Dict]
- **Purpose**: Split text into semantic chunks with metadata
- **Input**: Text content and source URL
- **Output**: List of chunks with metadata
- **Errors**: Text processing errors

### embed(text_chunks: List[Dict]) -> List[Tuple[str, List[float]]]
- **Purpose**: Generate embeddings for text chunks
- **Input**: List of text chunks
- **Output**: List of (content, embedding) tuples
- **Errors**: API errors, rate limits

### create_collection(collection_name: str)
- **Purpose**: Create Qdrant collection for embeddings
- **Input**: Name of collection to create
- **Output**: None
- **Errors**: Database connection errors

### save_chunk_to_qdrant(content: str, embedding: List[float], metadata: Dict, collection_name: str)
- **Purpose**: Save a text chunk with embedding to Qdrant
- **Input**: Content, embedding vector, metadata, collection name
- **Output**: Record ID
- **Errors**: Database errors

### main()
- **Purpose**: Execute the complete RAG ingestion pipeline
- **Input**: None (uses configured URLs and settings)
- **Output**: None (writes to Qdrant)
- **Errors**: Any errors from the pipeline steps