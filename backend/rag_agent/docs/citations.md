# Citation System Documentation

## Overview
The RAG Agent Service provides comprehensive citation information with every response, allowing users to understand the source of information and verify its accuracy. This documentation explains how citations work and how to consume them effectively.

## Citation Structure

Each response from the agent includes a `citations` array with detailed source information:

```json
{
  "citations": [
    {
      "id": "uuid-string",
      "source_url": "https://textbook.example.com/chapter/section",
      "chapter": "Chapter Title",
      "section": "Section Name",
      "heading": "Specific Heading",
      "page_reference": "p. 123",
      "similarity_score": 0.87,
      "text_excerpt": "Excerpt of the source text...",
      "source_type": "textbook",
      "confidence_score": 0.87,
      "citation_date": "2025-12-18T10:30:45.123456"
    }
  ]
}
```

### Field Descriptions

- **id**: Unique identifier for the citation
- **source_url**: Direct link to the source material
- **chapter**: Chapter name/identifier from the textbook
- **section**: Section name within the chapter
- **heading**: Specific heading within the section (from heading hierarchy)
- **page_reference**: Page number or location reference (if available)
- **similarity_score**: How semantically similar this source was to the query (0.0-1.0)
- **text_excerpt**: Excerpt of the text that supported the response
- **source_type**: Type of source (currently always "textbook")
- **confidence_score**: Confidence in the accuracy of this citation (0.0-1.0)
- **citation_date**: When this citation was created/used

## Using Citations

### For End Users
- Click on `source_url` to access the original content
- Check `similarity_score` and `confidence_score` to assess relevance
- Review `text_excerpt` to see the exact source material
- Use `chapter` and `section` information to locate content in physical textbooks

### For Developers
- Process the entire `citations` array to show all sources
- Sort citations by `similarity_score` to show most relevant sources first
- Validate citation completeness before displaying (all required fields present)
- Use `citation_date` to understand when information was accessed

## Citation Quality

### Confidence Scoring
- Scores of 0.7-1.0: High confidence, directly supports the response
- Scores of 0.4-0.69: Medium confidence, somewhat related to the response
- Scores below 0.4: Low confidence, tangentially related

### Completeness Validation
Citations are considered complete if they contain:
- `source_url` - Always required
- `chapter` - Always required
- `section` - Always required

Optional fields enhance the citation but aren't required for basic validity.

## Integration with Downstream Systems

### Web Applications
```javascript
// Display citations in a user-friendly format
function displayCitations(citations) {
  return citations.map(citation => `
    <div class="citation">
      <a href="${citation.source_url}">${citation.chapter} - ${citation.section}</a>
      <p class="excerpt">${citation.text_excerpt}</p>
      <div class="confidence">Confidence: ${(citation.confidence_score * 100).toFixed(0)}%</div>
    </div>
  `).join('');
}
```

### Academic Systems
- Use `page_reference` and `chapter`/`section` for formal citations
- Consider `confidence_score` when evaluating response reliability
- Store `citation_date` for temporal context of information access

### Content Management
- Track `source_url` usage to understand content demand
- Monitor `similarity_score` distribution to improve content indexing
- Analyze `text_excerpt` to identify frequently accessed content segments

## Best Practices

### For Consumption
- Always verify critical information by following source URLs
- Consider confidence scores when making important decisions
- Use multiple citations when available to get comprehensive context
- Note the citation date to understand when information was accessed

### For Validation
- Ensure citations correspond to actual retrieved content
- Validate that source URLs are accessible
- Check that confidence scores are within expected ranges (0.0-1.0)
- Verify that text excerpts accurately represent the source material

## Error Handling

If citations are missing or incomplete:
- The response may not be fully grounded in source material
- Consider requesting the information again
- Check if the question was too broad or ambiguous

If confidence scores are consistently low:
- The question may not have clear answers in the textbook
- Consider rephrasing the question
- The topic may not be covered in the current content

## API Integration

Citations are automatically included in all chat responses. No additional API calls are needed to retrieve citation information. The citation data is generated as part of the response process and validated before being returned to the client.

## Quality Assurance

The system validates citations through:
- Cross-referencing with retrieved content
- Confidence scoring based on semantic similarity
- Completeness checks for required fields
- URL validity verification

## Troubleshooting

Common issues and solutions:
- **Missing citations**: Question may not match any textbook content
- **Low confidence scores**: Question may be too general or ambiguous
- **Invalid URLs**: Source content may have moved or been removed
- **Empty text excerpts**: Source content may be too long to excerpt properly

For any citation-related issues, contact the system administrator with the specific citation ID and timestamp for investigation.