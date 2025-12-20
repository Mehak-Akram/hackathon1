import React from 'react';
import { validateChatMessage, validateSourceReference } from './models';
import { useI18n } from './LanguageProvider';
import './Chatbot.css';

/**
 * Component to display individual chat messages with proper formatting
 * Handles both user and assistant messages, including citations for assistant responses
 */
const ChatMessage = ({ message }) => {
  const { t } = useI18n();

  // Validate the message
  if (!validateChatMessage(message)) {
    console.error('Invalid message object:', message);
    return null;
  }

  const { role, content, sources, isLoading, isError, timestamp } = message;

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const renderCitations = () => {
    if (!sources || sources.length === 0) return null;

    // Filter and validate sources
    const validSources = sources.filter(source => validateSourceReference(source));

    if (validSources.length === 0) return null;

    // Sort citations by relevance (similarity score) if available, otherwise by confidence
    const sortedSources = [...validSources].sort((a, b) => {
      // Prioritize by similarity score if available
      if (a.similarity_score !== null && b.similarity_score !== null) {
        return b.similarity_score - a.similarity_score; // Higher scores first
      }
      // Fallback to confidence score if similarity is not available
      if (a.confidence_score !== null && b.confidence_score !== null) {
        return b.confidence_score - a.confidence_score; // Higher scores first
      }
      // If neither is available, maintain original order
      return 0;
    });

    return (
      <div className="message-citations">
        <h4>{t('citations.title')}</h4>
        <ul>
          {sortedSources.map((source, index) => (
            <li key={source.id || `source-${index}`} className="citation-item">
              <a
                href={source.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="citation-link"
              >
                {source.chapter}
                {source.section && `: ${source.section}`}
                {source.heading && ` - ${source.heading}`}
                {source.page_reference && ` (p. ${source.page_reference})`}
              </a>
              <div className="citation-metadata">
                {source.similarity_score !== null && source.similarity_score !== undefined && (
                  <span className="citation-score">{t('citations.relevance')} {(source.similarity_score * 100).toFixed(1)}%</span>
                )}
                {source.confidence_score !== null && source.confidence_score !== undefined && (
                  <span className="citation-confidence">{t('citations.confidence')} {(source.confidence_score * 100).toFixed(1)}%</span>
                )}
                {source.page_reference && (
                  <span className="citation-page">{t('citations.page')} {source.page_reference}</span>
                )}
              </div>
              {source.text_excerpt && (
                <div className="citation-excerpt">
                  <small>"{source.text_excerpt.substring(0, 150)}{source.text_excerpt.length > 150 ? '...' : ''}"</small>
                </div>
              )}
            </li>
          ))}
        </ul>
      </div>
    );
  };

  const getMessageClass = () => {
    let classes = `message message-${role}`;
    if (isLoading) classes += ' message-loading';
    if (isError) classes += ' message-error';
    return classes;
  };

  const renderFollowupSuggestions = () => {
    if (!message.followupSuggestions || message.followupSuggestions.length === 0) return null;

    return (
      <div className="message-followup-suggestions">
        <h4>{t('followup.title')}</h4>
        <ul className="followup-list">
          {message.followupSuggestions.map((suggestion, index) => (
            <li key={index} className="followup-item">
              <button
                className="followup-button"
                onClick={() => {
                  // This would trigger a callback to the parent to handle the suggestion
                  console.log('Follow-up suggestion clicked:', suggestion);
                }}
              >
                {suggestion}
              </button>
            </li>
          ))}
        </ul>
      </div>
    );
  };

  return (
    <div className={getMessageClass()}>
      <div className="message-header">
        <span className="message-role">{role === 'user' ? t('message.role.user', { defaultValue: 'You' }) : t('message.role.assistant', { defaultValue: 'Assistant' })}</span>
        <span className="message-timestamp">{formatTimestamp(timestamp)}</span>
      </div>
      <div className="message-content">
        {isLoading ? (
          <div className="loading-indicator">
            <div className="loading-dot"></div>
            <div className="loading-dot"></div>
            <div className="loading-dot"></div>
          </div>
        ) : (
          <>
            <p>{content}</p>
            {role === 'assistant' && renderCitations()}
            {role === 'assistant' && renderFollowupSuggestions()}
          </>
        )}
      </div>
    </div>
  );
};

export default ChatMessage;