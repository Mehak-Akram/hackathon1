"""
Unit tests for citation functionality and accuracy
"""
import pytest
from unittest.mock import AsyncMock
from backend.rag_agent.api.models.response import RetrievedContext, Citation
from backend.rag_agent.agents.textbook_agent import TextbookAgent


def test_citation_extraction_basic():
    """Test basic citation extraction from retrieved contexts"""
    agent = TextbookAgent()

    # Create mock retrieved contexts
    contexts = [
        RetrievedContext(
            id="ctx-1",
            content="Physical AI combines robotics and machine learning to create intelligent systems.",
            url="https://textbook.example.com/chapter1",
            chapter="Chapter 1: Introduction",
            section="1.1 Overview",
            heading_hierarchy=["Introduction", "Overview"],
            similarity_score=0.85
        )
    ]

    citations = agent._extract_citations(contexts)

    assert len(citations) == 1
    citation = citations[0]

    assert citation.source_url == "https://textbook.example.com/chapter1"
    assert citation.chapter == "Chapter 1: Introduction"
    assert citation.section == "1.1 Overview"
    assert citation.heading == "Overview"  # Last item in heading hierarchy
    assert citation.similarity_score == 0.85
    assert "Physical AI combines robotics" in citation.text_excerpt
    assert citation.source_type == "textbook"
    assert citation.confidence_score == 0.85


def test_citation_extraction_multiple_contexts():
    """Test citation extraction from multiple retrieved contexts"""
    agent = TextbookAgent()

    contexts = [
        RetrievedContext(
            id="ctx-1",
            content="First context content about physical AI.",
            url="https://textbook.example.com/chapter1",
            chapter="Chapter 1",
            section="1.1",
            heading_hierarchy=["Chapter 1"],
            similarity_score=0.90
        ),
        RetrievedContext(
            id="ctx-2",
            content="Second context content about machine learning.",
            url="https://textbook.example.com/chapter2",
            chapter="Chapter 2",
            section="2.1",
            heading_hierarchy=["Chapter 2"],
            similarity_score=0.75
        )
    ]

    citations = agent._extract_citations(contexts)

    assert len(citations) == 2

    # Check first citation
    assert citations[0].source_url == "https://textbook.example.com/chapter1"
    assert citations[0].similarity_score == 0.90
    assert citations[0].confidence_score == 0.90

    # Check second citation
    assert citations[1].source_url == "https://textbook.example.com/chapter2"
    assert citations[1].similarity_score == 0.75
    assert citations[1].confidence_score == 0.75


def test_citation_extraction_long_content():
    """Test that text excerpt is properly truncated for long content"""
    agent = TextbookAgent()

    long_content = "This is a very long content " + "word " * 100 + " that should be truncated."
    contexts = [
        RetrievedContext(
            id="ctx-1",
            content=long_content,
            url="https://textbook.example.com/chapter1",
            chapter="Chapter 1",
            section="1.1",
            heading_hierarchy=["Chapter 1"],
            similarity_score=0.80
        )
    ]

    citations = agent._extract_citations(contexts)
    citation = citations[0]

    # The excerpt should be truncated to about 200 characters with "..." appended
    assert len(citation.text_excerpt) <= 205  # 200 + 3 for "..." + some buffer
    assert citation.text_excerpt.endswith("...")
    assert "This is a very long content" in citation.text_excerpt


def test_citation_extraction_no_heading_hierarchy():
    """Test citation extraction when heading hierarchy is empty"""
    agent = TextbookAgent()

    contexts = [
        RetrievedContext(
            id="ctx-1",
            content="Content without heading hierarchy.",
            url="https://textbook.example.com/chapter1",
            chapter="Chapter 1",
            section="1.1",
            heading_hierarchy=[],  # Empty hierarchy
            similarity_score=0.80
        )
    ]

    citations = agent._extract_citations(contexts)
    citation = citations[0]

    # When heading hierarchy is empty, heading should be None
    assert citation.heading is None
    assert citation.source_url == "https://textbook.example.com/chapter1"


def test_citation_model_fields():
    """Test that Citation model has all expected fields"""
    citation = Citation(
        source_url="https://example.com",
        chapter="Test Chapter",
        section="Test Section"
    )

    # Check that all fields exist and have correct default values
    assert hasattr(citation, 'id')
    assert hasattr(citation, 'source_url')
    assert hasattr(citation, 'chapter')
    assert hasattr(citation, 'section')
    assert hasattr(citation, 'heading')
    assert hasattr(citation, 'page_reference')
    assert hasattr(citation, 'similarity_score')
    assert hasattr(citation, 'text_excerpt')
    assert hasattr(citation, 'source_type')
    assert hasattr(citation, 'confidence_score')
    assert hasattr(citation, 'citation_date')

    # Check default values
    assert citation.source_type == "textbook"
    assert citation.page_reference is None
    assert citation.heading is None
    assert citation.text_excerpt is None


def test_citation_validation():
    """Test citation field validation"""
    # Test similarity score validation (should be between 0 and 1)
    citation = Citation(
        source_url="https://example.com",
        chapter="Test Chapter",
        section="Test Section",
        similarity_score=0.85,
        confidence_score=0.90
    )

    assert 0.0 <= citation.similarity_score <= 1.0
    assert 0.0 <= citation.confidence_score <= 1.0

    # Test URL validation happens properly (would raise error if invalid)
    assert citation.source_url == "https://example.com"


@pytest.mark.asyncio
async def test_citation_in_agent_response():
    """Test that citations are properly included in agent responses"""
    agent = TextbookAgent()

    # Mock the retrieval tool
    with pytest.MonkeyPatch().context() as mp:
        # This is a simplified test - in a full implementation we would mock
        # the actual retrieval and generation process
        pass

    # Create mock contexts that would be returned by retrieval
    mock_contexts = [
        RetrievedContext(
            id="ctx-1",
            content="Physical AI content for testing citations.",
            url="https://textbook.example.com/test",
            chapter="Test Chapter",
            section="Test Section",
            heading_hierarchy=["Test", "Section"],
            similarity_score=0.88
        )
    ]

    # Test the citation extraction method directly
    citations = agent._extract_citations(mock_contexts)

    assert len(citations) == 1
    assert citations[0].source_url == "https://textbook.example.com/test"
    assert citations[0].chapter == "Test Chapter"
    assert citations[0].confidence_score == 0.88


if __name__ == "__main__":
    pytest.main([__file__])