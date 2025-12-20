/**
 * API service module to handle communication with backend endpoints
 */

/**
 * Send a message to the backend API
 * @param {string} backendUrl - Base URL for the backend API
 * @param {object} requestBody - Request body containing the question and context
 * @returns {Promise<object>} Response from the backend
 */
export const sendMessage = async (backendUrl, requestBody) => {
  try {
    // Ensure conversation history is properly formatted for the backend
    const processedRequestBody = {
      ...requestBody,
      // Include conversation history if available
      conversation_history: requestBody.conversation_history || [],
      // Ensure proper session context
      session_context: {
        session_id: requestBody.session_id,
        timestamp: new Date().toISOString(),
        ...requestBody.session_context
      }
    };

    const response = await fetch(`${backendUrl}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(processedRequestBody),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error sending message:', error);
    throw error;
  }
};

/**
 * Create a new session
 * @param {string} backendUrl - Base URL for the backend API
 * @returns {Promise<object>} Response containing the new session ID
 */
export const createSession = async (backendUrl) => {
  try {
    const response = await fetch(`${backendUrl}/session`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({}),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error creating session:', error);
    throw error;
  }
};

/**
 * Get session information
 * @param {string} backendUrl - Base URL for the backend API
 * @param {string} sessionId - Session ID to retrieve information for
 * @returns {Promise<object>} Response containing session information
 */
export const getSession = async (backendUrl, sessionId) => {
  try {
    const response = await fetch(`${backendUrl}/session/${sessionId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error getting session:', error);
    throw error;
  }
};

/**
 * Validate if the backend is accessible
 * @param {string} backendUrl - Base URL for the backend API
 * @returns {Promise<boolean>} True if backend is accessible, false otherwise
 */
export const isBackendAccessible = async (backendUrl) => {
  try {
    const response = await fetch(`${backendUrl}/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    return response.ok;
  } catch (error) {
    console.error('Error checking backend accessibility:', error);
    return false;
  }
};

/**
 * Get API configuration
 * @param {string} backendUrl - Base URL for the backend API
 * @returns {Promise<object>} Response containing API configuration
 */
export const getApiConfig = async (backendUrl) => {
  try {
    const response = await fetch(`${backendUrl}/config`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error getting API config:', error);
    throw error;
  }
};