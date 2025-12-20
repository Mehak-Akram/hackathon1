/**
 * Data models for frontend (ChatMessage, SourceReference interfaces)
 * Based on the API contracts for the chatbot UI component
 */

/**
 * ChatMessage interface
 * Represents a single message in the chat conversation
 * @typedef {Object} ChatMessage
 * @property {string} id - Unique identifier for the message (UUID)
 * @property {'user'|'assistant'} role - Message sender
 * @property {string} content - Message content
 * @property {string} timestamp - ISO 8601 timestamp
 * @property {SourceReference[]} [sources] - Source citations for assistant messages
 * @property {boolean} [isLoading] - Whether message is still loading (for assistant)
 * @property {boolean} [isError] - Whether this is an error message
 * @property {number} [responseTime] - Response time in seconds
 * @property {number} [retrievedContextCount] - Number of retrieved context items
 * @property {string[]} [followupSuggestions] - Follow-up question suggestions
 */

/**
 * SourceReference interface
 * Reference to a specific source in the textbook used in an assistant response
 * @typedef {Object} SourceReference
 * @property {string} id - Unique identifier (UUID)
 * @property {string} source_url - URL of the source
 * @property {string} chapter - Chapter name
 * @property {string} section - Section name
 * @property {string} [heading] - Specific heading
 * @property {string} [page_reference] - Page reference
 * @property {number} [similarity_score] - Relevance score (0.0-1.0)
 * @property {string} [text_excerpt] - Excerpt text
 * @property {string} [source_type] - Source type
 * @property {number} [confidence_score] - Confidence score (0.0-1.0)
 */

/**
 * PageContext interface
 * Context information about the page where the chat is embedded
 * @typedef {Object} PageContext
 * @property {string} url - URL of the current page
 * @property {string} title - Title of the current page
 * @property {string} [selectedText] - Text currently selected by the user
 * @property {string} pageTitle - Title of the document/page
 * @property {string} [pageContent] - Relevant content from the current page (truncated)
 * @property {Object} [documentMetadata] - Additional metadata about the document
 */

/**
 * UserPreferences interface
 * User preferences that influence the response style
 * @typedef {Object} UserPreferences
 * @property {'basic'|'intermediate'|'advanced'} [detailLevel] - Detail level
 * @property {'concise'|'detailed'|'examples'} [responseFormat] - Response format
 * @property {boolean} [includeCitations] - Whether to include source citations
 */

/**
 * ChatRequestFrontend interface
 * Request payload from the frontend with additional UI context
 * @typedef {Object} ChatRequestFrontend
 * @property {string} question - The user's question
 * @property {string} [session_id] - Session identifier for conversation context
 * @property {UserPreferences} [user_preferences] - User preferences for response style
 * @property {PageContext} [page_context] - Context about the current page
 * @property {string} [selected_text] - Text selected by the user
 */

/**
 * ChatResponse interface
 * Response from the backend API
 * @typedef {Object} ChatResponse
 * @property {string} response - The agent's response to the question
 * @property {string} session_id - The session identifier
 * @property {SourceReference[]} citations - List of source citations used in the response
 * @property {number} retrieved_context_count - Number of context chunks used
 * @property {number} response_time - Time taken to generate the response in seconds
 * @property {string[]} [followup_suggestions] - Suggested follow-up questions
 */

/**
 * Validates a ChatMessage object
 * @param {ChatMessage} message - The message to validate
 * @returns {boolean} True if valid, false otherwise
 */
export const validateChatMessage = (message) => {
  if (!message || typeof message !== 'object') return false;

  if (!message.id || typeof message.id !== 'string') return false;
  if (!['user', 'assistant'].includes(message.role)) return false;
  if (!message.content || typeof message.content !== 'string') return false;
  if (!message.timestamp || typeof message.timestamp !== 'string') return false;

  // Validate sources if present
  if (message.sources) {
    if (!Array.isArray(message.sources)) return false;
    if (!message.sources.every(source => validateSourceReference(source))) return false;
  }

  return true;
};

/**
 * Validates a SourceReference object
 * @param {SourceReference} source - The source reference to validate
 * @returns {boolean} True if valid, false otherwise
 */
export const validateSourceReference = (source) => {
  if (!source || typeof source !== 'object') return false;

  if (!source.id || typeof source.id !== 'string') return false;
  if (!source.source_url || typeof source.source_url !== 'string') return false;
  if (!source.chapter || typeof source.chapter !== 'string') return false;
  if (!source.section || typeof source.section !== 'string') return false;

  // Validate optional fields if present
  if (source.similarity_score !== undefined &&
      (typeof source.similarity_score !== 'number' ||
       source.similarity_score < 0 ||
       source.similarity_score > 1)) {
    return false;
  }

  if (source.confidence_score !== undefined &&
      (typeof source.confidence_score !== 'number' ||
       source.confidence_score < 0 ||
       source.confidence_score > 1)) {
    return false;
  }

  return true;
};

/**
 * Creates a new ChatMessage object
 * @param {'user'|'assistant'} role - The role of the message sender
 * @param {string} content - The message content
 * @param {Object} options - Additional options
 * @returns {ChatMessage} A new ChatMessage object
 */
export const createChatMessage = (role, content, options = {}) => {
  const {
    id = null,
    sources = [],
    isLoading = false,
    isError = false,
    responseTime = null,
    retrievedContextCount = null,
    followupSuggestions = []
  } = options;

  return {
    id: id || `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    role,
    content,
    timestamp: new Date().toISOString(),
    sources,
    isLoading,
    isError,
    responseTime,
    retrievedContextCount,
    followupSuggestions
  };
};

/**
 * Creates a new SourceReference object
 * @param {string} sourceUrl - The source URL
 * @param {string} chapter - The chapter name
 * @param {string} section - The section name
 * @param {Object} options - Additional options
 * @returns {SourceReference} A new SourceReference object
 */
export const createSourceReference = (sourceUrl, chapter, section, options = {}) => {
  const {
    id = null,
    heading = '',
    pageReference = '',
    similarityScore = null,
    textExcerpt = '',
    sourceType = 'textbook',
    confidenceScore = null
  } = options;

  return {
    id: id || `src_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    source_url: sourceUrl,
    chapter,
    section,
    heading,
    page_reference: pageReference,
    similarity_score: similarityScore,
    text_excerpt: textExcerpt,
    source_type: sourceType,
    confidence_score: confidenceScore
  };
};

/**
 * Validates page context
 * @param {PageContext} pageContext - The page context to validate
 * @returns {boolean} True if valid, false otherwise
 */
export const validatePageContext = (pageContext) => {
  if (!pageContext || typeof pageContext !== 'object') return false;

  if (!pageContext.url || typeof pageContext.url !== 'string') return false;
  if (!pageContext.title || typeof pageContext.title !== 'string') return false;

  // Validate selected text if present
  if (pageContext.selectedText && typeof pageContext.selectedText !== 'string') return false;

  return true;
};