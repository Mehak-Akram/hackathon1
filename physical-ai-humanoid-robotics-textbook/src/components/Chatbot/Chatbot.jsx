import React, { useState, useEffect, useRef } from 'react';
import ChatMessage from './ChatMessage';
import MessageInput from './MessageInput';
import { sendMessage, createSession, getSession } from './api';
import { generateUUID, isValidUUID, getPageContext } from './utils';
import { validateChatMessage, validateSourceReference, createChatMessage, createSourceReference } from './models';
import { useI18n } from './LanguageProvider';
import './Chatbot.css';

/**
 * Main Chatbot component that integrates with the Physical AI textbook Docusaurus site
 * Connects to FastAPI backend, passes page context and selected text, renders responses inline
 */
const Chatbot = ({
  backendUrl = 'http://localhost:8000/api/v1',
  initialSessionId,
  pageContext,
  userPreferences: initialUserPreferences,
  onSessionChange,
  onMessageReceived,
  className = '',
  style = {}
}) => {
  const { t } = useI18n();
  const [sessionId, setSessionId] = useState(initialSessionId || null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [userPreferences, setUserPreferences] = useState(() => {
    // Load user preferences from localStorage if available, fallback to props
    const savedPreferences = localStorage.getItem('chatbot-user-preferences');
    return savedPreferences ? JSON.parse(savedPreferences) : (initialUserPreferences || {});
  });
  const [showPreferences, setShowPreferences] = useState(false);
  const messagesEndRef = useRef(null);

  // Initialize session and restore from localStorage if available
  useEffect(() => {
    let isMounted = true;

    const initializeSession = async () => {
      // Try to restore session from localStorage
      const savedSession = localStorage.getItem('chatbot-session');
      if (savedSession) {
        try {
          const sessionData = JSON.parse(savedSession);
          if (sessionData.sessionId && sessionData.messages) {
            // Check if session is still valid (not older than 30 minutes)
            const sessionTime = new Date(sessionData.timestamp);
            const now = new Date();
            const diffInMinutes = (now - sessionTime) / (1000 * 60);

            if (diffInMinutes < 30 && isMounted) { // 30-minute session timeout
              setSessionId(sessionData.sessionId);
              setMessages(sessionData.messages);
              // Validate the restored session
              validateSession(sessionData.sessionId);
              return; // Exit early since we've restored the session
            } else {
              // Session expired, clear it
              localStorage.removeItem('chatbot-session');
            }
          }
        } catch (error) {
          console.error('Error restoring session from localStorage:', error);
        }
      }

      // If no valid session was restored from localStorage, use initialSessionId if provided
      // or create a new session if neither exists
      if (initialSessionId && isValidUUID(initialSessionId)) {
        if (isMounted) {
          setSessionId(initialSessionId);
          // Validate the provided session
          validateSession(initialSessionId);
        }
      } else {
        if (isMounted) {
          createNewSession();
        }
      }
    };

    initializeSession();

    return () => {
      isMounted = false;
    };
  }, []); // Empty dependency array to only run once on mount

  // Save session to localStorage whenever messages or sessionId changes
  useEffect(() => {
    if (sessionId && messages.length > 0) {
      const sessionData = {
        sessionId,
        messages,
        timestamp: new Date().toISOString()
      };
      localStorage.setItem('chatbot-session', JSON.stringify(sessionData));
    }
  }, [sessionId, messages]);

  // Save user preferences to localStorage whenever they change
  useEffect(() => {
    if (Object.keys(userPreferences).length > 0) {
      localStorage.setItem('chatbot-user-preferences', JSON.stringify(userPreferences));
    }
  }, [userPreferences]);

  // Validate session exists and is active
  const validateSession = async (id) => {
    try {
      const sessionInfo = await getSession(backendUrl, id);
      if (!sessionInfo.active) {
        // Session is no longer active, create a new one
        setSessionId(null);
        createNewSession();
      }
    } catch (err) {
      console.error('Session validation failed:', err);
      // If validation fails, create a new session
      setSessionId(null);
      createNewSession();
    }
  };

  // Scroll to bottom of messages when new messages are added
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Handle keyboard shortcuts and custom events
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ctrl/Cmd + K to focus on message input
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const inputElement = document.querySelector('.message-input-textarea');
        if (inputElement) {
          inputElement.focus();
        }
      }

      // Ctrl/Cmd + L to clear conversation
      if ((e.ctrlKey || e.metaKey) && e.key === 'l') {
        e.preventDefault();
        clearConversation();
      }

      // Escape key to close preferences panel
      if (e.key === 'Escape' && showPreferences) {
        setShowPreferences(false);
      }

      // Alt + P to toggle preferences panel
      if ((e.altKey || e.ctrlKey) && e.key === 'p') {
        e.preventDefault();
        setShowPreferences(!showPreferences);
      }

      // Alt + E to export conversation
      if ((e.altKey || e.ctrlKey) && e.key === 'e') {
        e.preventDefault();
        exportConversation();
      }
    };

    // Handle custom event to open chatbot
    const handleOpenChatbot = (e) => {
      // Focus on the message input when the chatbot is opened
      const inputElement = document.querySelector('.message-input-textarea');
      if (inputElement) {
        inputElement.focus();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    document.addEventListener('openChatbot', handleOpenChatbot);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('openChatbot', handleOpenChatbot);
    };
  }, [sessionId, showPreferences]);

  // Session timeout handling - check every 5 minutes, with 30-minute total session limit
  useEffect(() => {
    const sessionCheckInterval = setInterval(() => {
      if (sessionId) {
        validateSession(sessionId);
      }
    }, 5 * 60 * 1000); // Check every 5 minutes

    return () => clearInterval(sessionCheckInterval);
  }, [sessionId, backendUrl]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const createNewSession = async () => {
    try {
      const response = await createSession(backendUrl);
      const newSessionId = response.session_id;
      setSessionId(newSessionId);
      if (onSessionChange) {
        onSessionChange(newSessionId);
      }
    } catch (err) {
      setError('Failed to create session');
      console.error('Session creation error:', err);
    }
  };

  const handleSendMessage = async (question) => {
    if (!question.trim()) return;

    // Add user message to the conversation
    const userMessage = {
      id: generateUUID(),
      role: 'user',
      content: question,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      // Prepare the request with page context, user preferences, and conversation history
      const requestBody = {
        question: question,
        session_id: sessionId,
        user_preferences: userPreferences || {},
        page_context: {
          ...pageContext,
          ...getPageContext(1000), // Get full page context with 1000 char limit
        },
        // Include conversation history for context-aware responses
        conversation_history: messages.map(msg => ({
          role: msg.role,
          content: msg.content,
          timestamp: msg.timestamp
        }))
      };

      // Send the message to the backend
      const response = await sendMessage(backendUrl, requestBody);

      // Add the assistant's response to the conversation
      const assistantMessage = {
        id: generateUUID(),
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString(),
        sources: response.citations || [],
        responseTime: response.response_time,
        retrievedContextCount: response.retrieved_context_count,
        followupSuggestions: response.followup_suggestions || []
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Update session ID if it was created during this request
      if (response.session_id && response.session_id !== sessionId) {
        setSessionId(response.session_id);
        if (onSessionChange) {
          onSessionChange(response.session_id);
        }
      }

      if (onMessageReceived) {
        onMessageReceived(assistantMessage);
      }
    } catch (err) {
      setError('Failed to get response from the AI agent');
      console.error('Message sending error:', err);

      // Add error message to the conversation
      const errorMessage = {
        id: generateUUID(),
        role: 'assistant',
        content: 'Sorry, I encountered an error while processing your question. Please try again.',
        timestamp: new Date().toISOString(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearConversation = () => {
    setMessages([]);
    setError(null);
    // Clear session from localStorage as well
    localStorage.removeItem('chatbot-session');
    // Also clear any user preferences from localStorage if needed
    localStorage.removeItem('chatbot-user-preferences');
    createNewSession();
  };

  // Function to handle session timeout explicitly
  const handleSessionTimeout = () => {
    setMessages([]);
    setSessionId(null);
    localStorage.removeItem('chatbot-session');
    localStorage.removeItem('chatbot-user-preferences');
    setError('Session expired. Starting a new conversation.');
    createNewSession();
  };

  // Function to handle user preferences changes
  const handleUserPreferenceChange = (preference, value) => {
    setUserPreferences(prev => ({
      ...prev,
      [preference]: value
    }));
  };

  // Function to export conversation history
  const exportConversation = () => {
    if (messages.length === 0) {
      alert('No conversation history to export.');
      return;
    }

    // Create a structured export of the conversation
    const exportData = {
      sessionId,
      timestamp: new Date().toISOString(),
      messages: messages.map(msg => ({
        id: msg.id,
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp,
        sources: msg.sources || [],
        responseTime: msg.responseTime,
        retrievedContextCount: msg.retrievedContextCount,
        followupSuggestions: msg.followupSuggestions || []
      }))
    };

    // Convert to JSON string
    const jsonString = JSON.stringify(exportData, null, 2);

    // Create a blob and download link
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `chatbot-conversation-${sessionId || 'unknown'}-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className={`chatbot-container floating-chatbot ${className}`} style={style} role="application" aria-label={t('accessibility.chatLabel')}>
      <div className="chatbot-header" role="banner">
        <h3>{t('chatbot.title')}</h3>
        <div className="header-controls" role="toolbar" aria-label={t('accessibility.chatLabel')}>
          <button
            onClick={() => setShowPreferences(!showPreferences)}
            className="preferences-btn"
            title={t('chatbot.preferences')}
            aria-label={t('accessibility.preferencesButton')}
            aria-expanded={showPreferences}
          >
            ⚙️
          </button>
          <button
            onClick={exportConversation}
            className="export-btn"
            title={t('chatbot.export')}
            aria-label={t('accessibility.exportButton')}
          >
            📥
          </button>
          <button
            onClick={clearConversation}
            className="clear-session-btn"
            title={t('chatbot.clear')}
            aria-label={t('accessibility.clearButton')}
          >
            {t('chatbot.newChat')}
          </button>
        </div>
      </div>

      {showPreferences && (
        <div className="preferences-panel" role="dialog" aria-labelledby="preferences-title" aria-modal="true">
          <h4 id="preferences-title">{t('preferences.title')}</h4>
          <div className="preference-item">
            <label htmlFor="detail-level">{t('preferences.detailLevel')}</label>
            <select
              id="detail-level"
              value={userPreferences.detailLevel || 'medium'}
              onChange={(e) => handleUserPreferenceChange('detailLevel', e.target.value)}
              aria-label={t('preferences.detailLevel')}
            >
              <option value="low">{t('preferences.detailLevel.concise')}</option>
              <option value="medium">{t('preferences.detailLevel.balanced')}</option>
              <option value="high">{t('preferences.detailLevel.detailed')}</option>
            </select>
          </div>
          <div className="preference-item">
            <label htmlFor="response-format">{t('preferences.responseFormat')}</label>
            <select
              id="response-format"
              value={userPreferences.responseFormat || 'paragraph'}
              onChange={(e) => handleUserPreferenceChange('responseFormat', e.target.value)}
              aria-label={t('preferences.responseFormat')}
            >
              <option value="paragraph">{t('preferences.responseFormat.paragraph')}</option>
              <option value="bullet">{t('preferences.responseFormat.bullet')}</option>
              <option value="structured">{t('preferences.responseFormat.structured')}</option>
            </select>
          </div>
        </div>
      )}

      <div className="chat-messages" role="log" aria-live="polite" aria-label={t('accessibility.messagesLabel')}>
        {messages.length === 0 ? (
          <div className="welcome-message" role="status" aria-live="polite">
            <p>{t('chatbot.welcome')}</p>
            <p>{t('chatbot.welcome.desc')}</p>
            {showPreferences && (
              <p className="preferences-info">
                <small>{t('shortcuts.info')}</small>
              </p>
            )}
          </div>
        ) : (
          messages.map((message) => (
            <ChatMessage
              key={message.id}
              message={message}
            />
          ))
        )}
        {isLoading && (
          <ChatMessage
            message={{
              id: generateUUID(),
              role: 'assistant',
              content: t('loading.thinking'),
              timestamp: new Date().toISOString(),
              isLoading: true
            }}
          />
        )}
        <div ref={messagesEndRef} />
      </div>

      <MessageInput
        onSendMessage={handleSendMessage}
        disabled={isLoading}
        sessionId={sessionId}
        placeholder={t('chatbot.placeholder')}
      />

      {error && (
        <div className="chatbot-error">
          {error}
        </div>
      )}
    </div>
  );
};

export default Chatbot;