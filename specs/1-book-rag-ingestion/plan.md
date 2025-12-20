# Implementation Plan: RAG Spec 1 Execution Plan

**Feature**: Book Website RAG Ingestion Pipeline
**Branch**: 1-book-rag-ingestion
**Created**: 2025-12-17
**Status**: Draft

## Technical Context

The implementation will create a RAG ingestion pipeline that:
- Crawls the deployed Docusaurus site at https://hackathon1-7k7o.vercel.app/
- Extracts content, chunks it, and generates embeddings using Cohere
- Stores embeddings with metadata in Qdrant Cloud
- All implementation will be in a single main.py file with specified functions

### Technology Stack
- Python 3.9+
- uv for package management
- requests/beautifulsoup4 for web scraping
- Cohere API for embeddings
- Qdrant Cloud for vector storage
- Docusaurus site as data source

### Dependencies to Install
- python-dotenv
- requests
- beautifulsoup4
- cohere
- qdrant-client
- lxml

### Architecture Overview
```
[Website URLs] → [Content Extraction] → [Text Chunking] → [Embeddings] → [Qdrant Storage]
```
-**SiteMap url** :  https://hackathon1-7k7o.vercel.app/sitemap.xml

## Constitution Check

Based on `.specify/memory/constitution.md`, this implementation will:
- ✅ Follow code quality standards with clean, maintainable code
- ✅ Use secure handling of API keys and sensitive data
- ✅ Include proper error handling and logging
- ✅ Follow performance and reliability principles
- ✅ Maintain compatibility with downstream systems

## Gates

### Gate 1: Technical Feasibility
✅ Confirmed - All required technologies are available and compatible

### Gate 2: Resource Availability
✅ Confirmed - APIs and services (Cohere, Qdrant) are accessible

### Gate 3: Architecture Alignment
✅ Confirmed - Solution aligns with feature requirements

### Gate 4: Security & Compliance
✅ Confirmed - Will use environment variables for sensitive data

## Phase 0: Research

### Research Tasks
1. Best practices for web scraping Docusaurus sites
2. Optimal text chunking strategies for RAG
3. Cohere embedding model selection and usage
4. Qdrant Cloud setup and collection management
5. Error handling patterns for web crawling

## Phase 1: Design & Contracts

### Data Model
- Text Chunk: content, metadata (URL, chapter, section, heading hierarchy)
- Embedding Vector: numerical representation + metadata
- Collection: ragchtbot_embadding with proper indexing

### API Contract
- Single main.py file with functions:
  - get_all_urls(base_url): List of all content URLs
  - extract_text_from_url(url): Extracted clean text content
  - chunk_text(text): List of text chunks with metadata
  - embed(text_chunks): Embeddings for each chunk
  - create_collection(collection_name): Setup Qdrant collection
  - save_chunk_to_qdrant(chunk, embedding): Store in Qdrant
  - main(): Execute full pipeline

## Phase 2: Implementation Plan

### Step 1: Project Setup
- Create backend/ directory
- Initialize with uv
- Set up environment variables
- Install dependencies

### Step 2: Web Scraping Module
- Implement get_all_urls function
- Implement extract_text_from_url function
- Handle Docusaurus site structure

### Step 3: Text Processing
- Implement chunk_text function with heading-aware strategy
- Preserve document hierarchy in metadata

### Step 4: Embedding Generation
- Implement embed function using Cohere API
- Handle API rate limits and errors

### Step 5: Vector Storage
- Implement Qdrant integration
- Create ragchtbot_embadding collection
- Implement save_chunk_to_qdrant function

### Step 6: Integration & Validation
- Create main function that executes the full pipeline
- Add validation and error handling
- Test with https://hackathon1-7k7o.vercel.app/