# Research Document: RAG Ingestion Pipeline

## Decision: Web Scraping Approach for Docusaurus Sites
**Rationale**: Docusaurus sites typically have predictable structure with navigation elements that can be scraped to discover all content pages. Using requests and BeautifulSoup is lightweight and effective for static site crawling.
**Alternatives considered**:
- Selenium for JavaScript-heavy sites (overkill for Docusaurus)
- Direct API access (not available for static sites)
- Scraping tools like Scrapy (unnecessary complexity)

## Decision: Text Chunking Strategy
**Rationale**: For RAG applications, semantic chunking that respects document hierarchy (headings, sections) performs better than fixed-size token chunks. This preserves context and enables better retrieval.
**Alternatives considered**:
- Fixed token length chunks (loses document structure)
- Sentence-level chunks (may break semantic coherence)
- Recursive splitting (more complex, less context-aware)

## Decision: Cohere Embedding Model Selection
**Rationale**: Cohere's embed-multilingual-v3.0 model offers good balance of performance and cost for technical content like textbooks. It handles mixed-language content well and is production-ready.
**Alternatives considered**:
- embed-english-v3.0 (limited to English content)
- Older v2 models (less capable)
- Alternative providers (OpenAI, Google) (would violate constraint)

## Decision: Qdrant Collection Design
**Rationale**: Creating a dedicated collection named "ragchtbot_embadding" with proper payload schema for metadata storage ensures efficient querying and proper organization of embeddings.
**Alternatives considered**:
- Generic collection names (less organized)
- Multiple collections by topic (unnecessary complexity)
- Different vector dimensionality (would affect performance)

## Decision: Error Handling Strategy
**Rationale**: Implementing graceful degradation with detailed logging allows the pipeline to continue processing when individual pages fail, while providing diagnostics for troubleshooting.
**Alternatives considered**:
- Stop on first error (fragile)
- Silent failure (no visibility into problems)
- Basic exception handling (insufficient diagnostic info)

## Best Practices Applied
1. Environment variable management for API keys
2. Connection pooling for web requests
3. Batch processing for embedding generation
4. Proper cleanup of resources
5. Comprehensive logging for debugging