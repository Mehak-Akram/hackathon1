/**
 * Utility functions for the Chatbot component
 */

/**
 * Generate a UUID string
 * @returns {string} A UUID string
 */
export const generateUUID = () => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
};

/**
 * Validate if a string is a valid UUID
 * @param {string} uuid - The string to validate
 * @returns {boolean} True if the string is a valid UUID, false otherwise
 */
export const isValidUUID = (uuid) => {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  return uuidRegex.test(uuid);
};

/**
 * Validate if a string is a valid URL
 * @param {string} url - The string to validate
 * @returns {boolean} True if the string is a valid URL, false otherwise
 */
export const isValidURL = (url) => {
  try {
    new URL(url);
    return true;
  } catch (e) {
    return false;
  }
};

/**
 * Truncate text to a specified length
 * @param {string} text - The text to truncate
 * @param {number} maxLength - Maximum length of the text
 * @returns {string} Truncated text with ellipsis if needed
 */
export const truncateText = (text, maxLength = 1000) => {
  if (!text || typeof text !== 'string') {
    return '';
  }

  if (text.length <= maxLength) {
    return text;
  }

  return text.substring(0, maxLength) + '...';
};

/**
 * Format a timestamp to a readable string
 * @param {string} timestamp - ISO string timestamp
 * @returns {string} Formatted time string
 */
export const formatTimestamp = (timestamp) => {
  if (!timestamp) return '';

  const date = new Date(timestamp);
  const now = new Date();
  const diffInSeconds = Math.floor((now - date) / 1000);

  if (diffInSeconds < 60) {
    return 'Just now';
  } else if (diffInSeconds < 3600) {
    const minutes = Math.floor(diffInSeconds / 60);
    return `${minutes}m ago`;
  } else if (diffInSeconds < 86400) {
    const hours = Math.floor(diffInSeconds / 3600);
    return `${hours}h ago`;
  } else {
    const days = Math.floor(diffInSeconds / 86400);
    return `${days}d ago`;
  }
};

/**
 * Sanitize HTML content to prevent XSS
 * @param {string} content - The content to sanitize
 * @returns {string} Sanitized content
 */
export const sanitizeHTML = (content) => {
  if (!content || typeof content !== 'string') {
    return '';
  }

  // Basic HTML sanitization - in a real application, use a proper library like DOMPurify
  return content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;');
};

/**
 * Extract selected text from the page with optional truncation
 * @param {number} maxLength - Maximum length of selected text (default: 1000)
 * @returns {string} The currently selected text (truncated if necessary)
 */
export const getSelectedText = (maxLength = 1000) => {
  const selection = window.getSelection?.();
  let selectedText = selection ? selection.toString().trim() : '';

  // Truncate selected text to prevent large payloads
  if (selectedText.length > maxLength) {
    selectedText = truncateText(selectedText, maxLength);
  }

  return selectedText;
};

/**
 * Get current page context
 * @param {number} maxContentLength - Maximum length of page content (default: 1000)
 * @returns {object} Page context information
 */
export const getPageContext = (maxContentLength = 1000) => {
  return {
    url: window.location.href,
    title: document.title,
    selectedText: getSelectedText(maxContentLength),
    pageTitle: document.title,
    pageContent: truncateText(document.body?.innerText || '', maxContentLength),
    documentMetadata: {
      userAgent: navigator.userAgent,
      timestamp: new Date().toISOString(),
      referrer: document.referrer,
      language: navigator.language,
      platform: navigator.platform,
      viewport: {
        width: window.innerWidth,
        height: window.innerHeight
      }
    }
  };
};

/**
 * Deep clone an object
 * @param {object} obj - The object to clone
 * @returns {object} A deep clone of the object
 */
export const deepClone = (obj) => {
  if (obj === null || typeof obj !== 'object') {
    return obj;
  }

  if (obj instanceof Date) {
    return new Date(obj.getTime());
  }

  if (obj instanceof Array) {
    return obj.map(item => deepClone(item));
  }

  const clonedObj = {};
  for (const key in obj) {
    if (obj.hasOwnProperty(key)) {
      clonedObj[key] = deepClone(obj[key]);
    }
  }

  return clonedObj;
};

/**
 * Debounce a function
 * @param {function} func - The function to debounce
 * @param {number} wait - Time to wait in milliseconds
 * @returns {function} Debounced function
 */
export const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};