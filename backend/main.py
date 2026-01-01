import os
import re
import uuid
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import cohere
from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv
import time
import logging
from typing import List, Dict, Tuple

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_all_urls(base_url: str) -> List[str]:
    """
    Crawl the Docusaurus site and collect all content URLs
    """
    logger.info(f"Starting to crawl: {base_url}")
    urls = set()

    try:
        response = requests.get(base_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all links on the page
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)

            # Only add URLs from the same domain and that look like content pages
            if urlparse(full_url).netloc == urlparse(base_url).netloc:
                if (full_url.endswith('/') or full_url.endswith('.html')) and '#' not in full_url:
                    urls.add(full_url)

        # Also check for sitemap if it exists
        sitemap_url = urljoin(base_url, 'sitemap.xml')
        try:
            sitemap_response = requests.get(sitemap_url)
            if sitemap_response.status_code == 200:
                sitemap_soup = BeautifulSoup(sitemap_response.content, 'xml')
                for loc in sitemap_soup.find_all('loc'):
                    url = loc.text.strip()
                    if urlparse(url).netloc == urlparse(base_url).netloc:
                        urls.add(url)
        except Exception as e:
            logger.warning(f"Sitemap not found or accessible: {e}")

        logger.info(f"Found {len(urls)} URLs")
        return list(urls)

    except Exception as e:
        logger.error(f"Error crawling {base_url}: {str(e)}")
        raise

def extract_text_from_url(url: str) -> str:
    """
    Extract clean text content from a URL with enhanced Docusaurus-specific handling
    """
    logger.info(f"Extracting text from: {url}")

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove unwanted elements
        for element in soup(["script", "style", "nav", "header", "footer", "aside", ".theme-edit-this-page", ".theme-last-updated"]):
            element.decompose()

        # Try to find main content area (Docusaurus specific selectors)
        content_selectors = [
            'main .container article',  # Docusaurus main content
            '.theme-doc-markdown',      # Docusaurus markdown content
            '.markdown',                # Markdown content area
            'article',                  # Article content
            '.docPageContainer',        # Docusaurus doc container
            '.container .col',          # Docusaurus content column
            'main',                     # Main content area
        ]

        text_content = ""
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # Extract text while preserving structure
                text_content = extract_meaningful_text(content_elem)
                break

        # If no specific content area found, get body content
        if not text_content:
            body = soup.find('body')
            if body:
                text_content = extract_meaningful_text(body)
            else:
                text_content = soup.get_text(separator=' ', strip=True)

        # Clean up excessive whitespace
        text_content = re.sub(r'\s+', ' ', text_content).strip()

        logger.info(f"Extracted {len(text_content)} characters from {url}")
        return text_content

    except Exception as e:
        logger.error(f"Error extracting text from {url}: {str(e)}")
        raise

def extract_meaningful_text(element):
    """
    Extract meaningful text from a BeautifulSoup element, preserving structure
    """
    # Get all text but preserve important structural elements
    parts = []

    for item in element.descendants:
        if item.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            # Add headings with special formatting
            heading_text = item.get_text(separator=' ', strip=True)
            if heading_text:
                parts.append(f"\n#{'#' * (int(item.name[1]) - 1)} {heading_text}\n")
        elif item.name == 'p':
            # Add paragraphs
            para_text = item.get_text(separator=' ', strip=True)
            if para_text:
                parts.append(para_text + "\n")
        elif item.name in ['li']:
            # Add list items
            li_text = item.get_text(separator=' ', strip=True)
            if li_text:
                parts.append(f"• {li_text}\n")
        elif item.name in ['div', 'span']:
            # Add text from divs and spans only if they're not containers for other content
            if not item.find(['div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                text = item.get_text(separator=' ', strip=True)
                if text and len(text) > 20:  # Only add substantial text
                    parts.append(text + " ")
        elif isinstance(item, str) and item.strip():
            # Add text nodes directly
            text = item.strip()
            if text:
                parts.append(text + " ")

    return " ".join(parts).strip()

def chunk_text(text: str, url: str = "") -> List[Dict]:
    """
    Chunk text using advanced semantic chunking strategy for better RAG performance
    """
    logger.info(f"Chunking text of {len(text)} characters using semantic chunking")

    # Extract basic metadata from URL
    parsed_url = urlparse(url)
    path_parts = [part for part in parsed_url.path.split('/') if part]
    if len(path_parts) >= 1:
        chapter = path_parts[-1] if path_parts[-1] else (path_parts[-2] if len(path_parts) > 1 else "home")
    else:
        chapter = "home"

    # Import the semantic chunker
    from rag_agent.utils.semantic_chunker import semantic_chunker

    # Create metadata for the text using proper schema
    from rag_agent.utils.metadata_schema import ChunkMetadata

    base_metadata = ChunkMetadata(
        url=url,
        chapter=chapter,
        section="",
        heading_hierarchy=[],
        source_type="web"
    )

    # Use the semantic chunker to create properly structured chunks
    chunks = semantic_chunker.create_chunks(text, url=url, metadata=base_metadata)

    # Convert to the format expected by the rest of the pipeline
    formatted_chunks = []
    for i, chunk in enumerate(chunks):
        # Calculate quality score for the chunk
        quality_score = semantic_chunker.calculate_chunk_quality(chunk.content)

        # Update metadata with quality metrics
        chunk.metadata.quality_score = quality_score

        formatted_chunk = {
            "content": chunk.content,
            "metadata": chunk.metadata
        }
        formatted_chunks.append(formatted_chunk)

    logger.info(f"Created {len(formatted_chunks)} semantic chunks from text")
    return formatted_chunks

def embed(text_chunks: List[Dict]) -> List[Tuple[str, List[float]]]:
    """
    Generate embeddings using Cohere API
    """
    logger.info(f"Generating embeddings for {len(text_chunks)} chunks")

    # Initialize Cohere client
    cohere_api_key = os.getenv("COHERE_API_KEY")
    if not cohere_api_key:
        raise ValueError("COHERE_API_KEY environment variable not set")

    co = cohere.Client(cohere_api_key)

    # Prepare texts for embedding (just the content part)
    texts = [chunk["content"] for chunk in text_chunks]

    try:
        # Generate embeddings in batches (Cohere API has limits)
        batch_size = 96  # Cohere's max batch size is 96
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = co.embed(
                texts=batch,
                model="embed-multilingual-v3.0",  # Using multilingual model for broader compatibility
                input_type="search_document"
            )

            batch_embeddings = response.embeddings
            all_embeddings.extend(batch_embeddings)

            # Rate limiting - be respectful to the API
            time.sleep(0.1)

        # Pair each chunk with its embedding
        result = []
        for i, chunk in enumerate(text_chunks):
            result.append((chunk["content"], all_embeddings[i]))

        logger.info(f"Generated {len(result)} embeddings successfully")
        return result

    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        raise

def create_collection(collection_name: str):
    """
    Create Qdrant collection with proper schema
    """
    logger.info(f"Creating Qdrant collection: {collection_name}")

    # Initialize Qdrant client
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")

    if not qdrant_url or not qdrant_api_key:
        raise ValueError("QDRANT_URL and QDRANT_API_KEY environment variables must be set")

    client = QdrantClient(
        url=qdrant_url,
        api_key=qdrant_api_key,
        prefer_grpc=False  # Using HTTP for simplicity
    )

    try:
        # Check if collection already exists
        try:
            client.get_collection(collection_name)
            logger.info(f"Collection {collection_name} already exists, skipping creation")
            return
        except:
            # Collection doesn't exist, create it
            pass

        # Create collection with appropriate vector size for Cohere embeddings
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=1024,  # Cohere embed-multilingual-v3.0 produces 1024-dimensional vectors
                distance=models.Distance.COSINE
            )
        )

        logger.info(f"Collection {collection_name} created successfully")

    except Exception as e:
        logger.error(f"Error creating collection: {str(e)}")
        raise

def save_chunk_to_qdrant(content: str, embedding: List[float], metadata: Dict, collection_name: str):
    """
    Save a single chunk with its embedding to Qdrant
    """
    logger.info(f"Saving chunk to Qdrant collection: {collection_name}")

    # Initialize Qdrant client
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")

    if not qdrant_url or not qdrant_api_key:
        raise ValueError("QDRANT_URL and QDRANT_API_KEY environment variables must be set")

    client = QdrantClient(
        url=qdrant_url,
        api_key=qdrant_api_key,
        prefer_grpc=False
    )

    try:
        # Generate a unique ID for this record
        record_id = str(uuid.uuid4())

        # Prepare the point to insert
        point = models.PointStruct(
            id=record_id,
            vector=embedding,
            payload={
                "content": content,
                "url": metadata.get("url", ""),
                "chapter": metadata.get("chapter", ""),
                "section": metadata.get("section", ""),
                "heading_hierarchy": metadata.get("heading_hierarchy", []),
                "text_chunk_id": record_id
            }
        )

        # Upsert the point to Qdrant
        client.upsert(
            collection_name=collection_name,
            points=[point]
        )

        logger.info(f"Saved chunk to Qdrant with ID: {record_id}")
        return record_id

    except Exception as e:
        logger.error(f"Error saving chunk to Qdrant: {str(e)}")
        raise

def main():
    """
    Main function to execute the full RAG ingestion pipeline
    """
    logger.info("Starting RAG ingestion pipeline")

    # Configuration - using environment variable or default
    base_url = os.getenv("DOCUSAURUS_BASE_URL", "https://hackathon1-7k7o.vercel.app/")
    collection_name = "ragchtbot_embadding"

    try:
        logger.info(f"Starting ingestion from base URL: {base_url}")

        # Step 1: Get all URLs from the Docusaurus site
        urls = get_all_urls(base_url)
        logger.info(f"Discovered {len(urls)} URLs to process")

        if not urls:
            logger.warning("No URLs found to process. Check the base URL and network connectivity.")
            return

        # Step 2: Process each URL
        all_chunks = []
        processed_urls = 0

        for i, url in enumerate(urls):
            logger.info(f"Processing URL {i+1}/{len(urls)}: {url}")

            try:
                # Extract text from URL
                text = extract_text_from_url(url)

                if not text.strip():
                    logger.warning(f"No content extracted from {url}, skipping...")
                    continue

                # Chunk the text
                chunks = chunk_text(text, url)

                logger.info(f"Created {len(chunks)} chunks from {url}")

                # Add to all chunks
                for chunk in chunks:
                    all_chunks.append({
                        "content": chunk["content"],
                        "metadata": chunk["metadata"]
                    })

                processed_urls += 1

                # Optional: Add delay to be respectful to the server
                time.sleep(0.1)

            except requests.exceptions.RequestException as e:
                logger.error(f"Network error processing URL {url}: {str(e)}")
                continue  # Continue with other URLs
            except Exception as e:
                logger.error(f"Error processing URL {url}: {str(e)}")
                continue  # Continue with other URLs

        logger.info(f"Successfully processed {processed_urls} URLs")
        logger.info(f"Total chunks created: {len(all_chunks)}")

        if not all_chunks:
            logger.error("No chunks were created. Pipeline cannot continue.")
            return

        # Step 3: Create Qdrant collection
        logger.info("Setting up Qdrant collection...")
        create_collection(collection_name)

        # Step 4: Generate embeddings for all chunks
        logger.info("Generating embeddings for all chunks...")
        embedded_chunks = embed(all_chunks)

        # Step 5: Save each chunk with embedding to Qdrant
        saved_count = 0
        failed_count = 0

        for i, (content, embedding) in enumerate(embedded_chunks):
            try:
                # Find the original chunk to get metadata
                # Use index instead of searching by content to avoid issues with duplicate content
                if i < len(all_chunks):
                    original_chunk = all_chunks[i]

                    save_chunk_to_qdrant(
                        content=content,
                        embedding=embedding,
                        metadata=original_chunk["metadata"],
                        collection_name=collection_name
                    )
                    saved_count += 1

                    if saved_count % 10 == 0:  # Log progress every 10 saves
                        logger.info(f"Progress: {saved_count}/{len(embedded_chunks)} chunks saved")

            except Exception as e:
                logger.error(f"Error saving chunk {i+1}: {str(e)}")
                failed_count += 1
                continue

        logger.info(f"Successfully saved {saved_count} chunks to Qdrant")
        if failed_count > 0:
            logger.warning(f"Failed to save {failed_count} chunks")

        # Step 6: Validation
        logger.info("Performing validation...")

        # Initialize Qdrant client for validation
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")

        if not qdrant_url or not qdrant_api_key:
            logger.error("QDRANT_URL and QDRANT_API_KEY must be set for validation")
            return

        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)

        # Count total points in collection
        count_result = client.count(collection_name=collection_name)
        logger.info(f"Total points in collection: {count_result.count}")

        # Perform a simple test query to verify vectors are accessible
        try:
            # Get one point to verify data is stored correctly
            points, _ = client.scroll(
                collection_name=collection_name,
                limit=1
            )
            if points:
                sample_point = points[0]
                logger.info(f"Sample point ID: {sample_point.id}")
                logger.info(f"Sample point payload keys: {list(sample_point.payload.keys())}")
                logger.info("✓ Vectors are successfully stored and accessible in Qdrant")
        except Exception as e:
            logger.error(f"Error during validation query: {str(e)}")

        logger.info("RAG ingestion pipeline completed successfully!")
        logger.info(f"Summary: Processed {processed_urls} URLs, created {len(all_chunks)} chunks, saved {saved_count} to Qdrant")

    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        raise

# For running the ingestion pipeline separately, use: python -c "from main import main; main()"
if __name__ == "__main__":
    import uvicorn
    # Only start the web server when run directly, not the ingestion pipeline
    from rag_agent.main import app
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False  # Set reload to False for production
    )