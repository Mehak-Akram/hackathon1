# Data Model: RAG Ingestion Pipeline

## Entities

### Text Chunk
- **id**: string (unique identifier for the chunk)
- **content**: string (the actual text content)
- **url**: string (source URL of the content)
- **chapter**: string (chapter name/identifier from hierarchy)
- **section**: string (section name within chapter)
- **heading_hierarchy**: list[string] (hierarchy of headings from the document)
- **position**: integer (position in the original document)
- **metadata**: dict (additional metadata as key-value pairs)

### Embedding Vector
- **id**: string (corresponds to the text chunk ID)
- **vector**: list[float] (numerical embedding representation)
- **text_chunk_id**: string (foreign key to Text Chunk)
- **model**: string (embedding model used to generate this vector)

### Qdrant Point
- **id**: string (unique identifier for the Qdrant point)
- **vector**: list[float] (embedding vector)
- **payload**: dict (metadata including URL, chapter, section, etc.)
  - url: string
  - chapter: string
  - section: string
  - heading_hierarchy: list[string]
  - content: string

### Collection Schema (ragchtbot_embadding)
- **Collection Name**: ragchtbot_embadding
- **Vector Size**: 1024 (for Cohere embed-multilingual-v3.0 with float type)
- **Distance Metric**: Cosine
- **Payload Schema**:
  - url: keyword
  - chapter: keyword
  - section: keyword
  - heading_hierarchy: text
  - content: text
  - text_chunk_id: keyword