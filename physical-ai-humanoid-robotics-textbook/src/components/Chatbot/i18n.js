/**
 * Internationalization (i18n) module for the Chatbot component
 * Provides multilingual support infrastructure
 */

// Default language
const DEFAULT_LANGUAGE = 'en';

// Supported languages
const SUPPORTED_LANGUAGES = ['en', 'es', 'fr', 'de', 'zh', 'ja'];

// Translation resources
const TRANSLATIONS = {
  en: {
    // Chatbot interface
    'chatbot.title': 'Physical AI Textbook Assistant',
    'chatbot.newChat': 'New Chat',
    'chatbot.preferences': 'Preferences',
    'chatbot.export': 'Export',
    'chatbot.clear': 'Clear Conversation',
    'chatbot.welcome': 'Hello! I\'m your Physical AI textbook assistant.',
    'chatbot.welcome.desc': 'Ask me any questions about Physical AI concepts, and I\'ll provide answers grounded in the textbook content with proper citations.',
    'chatbot.placeholder': 'Ask a question about Physical AI concepts...',
    'chatbot.send': 'Send',

    // Preferences
    'preferences.title': 'Preferences',
    'preferences.detailLevel': 'Detail Level:',
    'preferences.detailLevel.concise': 'Concise',
    'preferences.detailLevel.balanced': 'Balanced',
    'preferences.detailLevel.detailed': 'Detailed',
    'preferences.responseFormat': 'Response Format:',
    'preferences.responseFormat.paragraph': 'Paragraph',
    'preferences.responseFormat.bullet': 'Bullet Points',
    'preferences.responseFormat.structured': 'Structured',

    // Citations
    'citations.title': 'Sources:',
    'citations.relevance': 'Relevance:',
    'citations.confidence': 'Confidence:',
    'citations.page': 'Page:',

    // Follow-up suggestions
    'followup.title': 'Suggested follow-up questions:',

    // Loading states
    'loading.thinking': 'Thinking...',

    // Error messages
    'error.session': 'Session expired. Starting a new conversation.',
    'error.response': 'Sorry, I encountered an error while processing your question. Please try again.',
    'error.noExport': 'No conversation history to export.',

    // Keyboard shortcuts
    'shortcuts.info': 'Keyboard shortcuts: Ctrl/Cmd+K to focus input, Ctrl/Cmd+L to clear, Alt+P to toggle preferences, Alt+E to export',

    // Accessibility
    'accessibility.chatLabel': 'AI Chatbot Interface',
    'accessibility.messagesLabel': 'Chat conversation',
    'accessibility.inputLabel': 'Message input',
    'accessibility.sendButton': 'Send message',
    'accessibility.preferencesButton': 'Open preferences',
    'accessibility.exportButton': 'Export conversation',
    'accessibility.clearButton': 'Clear conversation',

    // Export
    'export.filename': 'chatbot-conversation',

    // Detail level descriptions
    'detail.low': 'Brief and concise responses',
    'detail.medium': 'Balanced level of detail',
    'detail.high': 'Comprehensive and detailed responses',

    // Message roles
    'message.role.user': 'You',
    'message.role.assistant': 'Assistant'
  },
  es: {
    // Spanish translations
    'chatbot.title': 'Asistente del libro de texto de IA Física',
    'chatbot.newChat': 'Nueva Conversación',
    'chatbot.preferences': 'Preferencias',
    'chatbot.export': 'Exportar',
    'chatbot.clear': 'Limpiar Conversación',
    'chatbot.welcome': '¡Hola! Soy tu asistente del libro de texto de IA Física.',
    'chatbot.welcome.desc': 'Hazme preguntas sobre conceptos de IA Física y te proporcionaré respuestas basadas en el contenido del libro con citas adecuadas.',
    'chatbot.placeholder': 'Haz una pregunta sobre conceptos de IA Física...',
    'chatbot.send': 'Enviar',

    // Preferences
    'preferences.title': 'Preferencias',
    'preferences.detailLevel': 'Nivel de Detalle:',
    'preferences.detailLevel.concise': 'Conciso',
    'preferences.detailLevel.balanced': 'Equilibrado',
    'preferences.detailLevel.detailed': 'Detallado',
    'preferences.responseFormat': 'Formato de Respuesta:',
    'preferences.responseFormat.paragraph': 'Párrafo',
    'preferences.responseFormat.bullet': 'Puntos',
    'preferences.responseFormat.structured': 'Estructurado',

    // Citations
    'citations.title': 'Fuentes:',
    'citations.relevance': 'Relevancia:',
    'citations.confidence': 'Confianza:',
    'citations.page': 'Página:',

    // Follow-up suggestions
    'followup.title': 'Preguntas sugeridas:',

    // Loading states
    'loading.thinking': 'Pensando...',

    // Error messages
    'error.session': 'Sesión expirada. Iniciando nueva conversación.',
    'error.response': 'Lo siento, encontré un error al procesar tu pregunta. Por favor intenta de nuevo.',
    'error.noExport': 'No hay historial de conversación para exportar.',

    // Keyboard shortcuts
    'shortcuts.info': 'Atajos de teclado: Ctrl/Cmd+K para enfocar entrada, Ctrl/Cmd+L para limpiar, Alt+P para preferencias, Alt+E para exportar',

    // Accessibility
    'accessibility.chatLabel': 'Interfaz de Chatbot de IA',
    'accessibility.messagesLabel': 'Conversación de chat',
    'accessibility.inputLabel': 'Entrada de mensaje',
    'accessibility.sendButton': 'Enviar mensaje',
    'accessibility.preferencesButton': 'Abrir preferencias',
    'accessibility.exportButton': 'Exportar conversación',
    'accessibility.clearButton': 'Limpiar conversación',

    // Export
    'export.filename': 'chatbot-conversacion',

    // Detail level descriptions
    'detail.low': 'Respuestas breves y concisas',
    'detail.medium': 'Nivel equilibrado de detalle',
    'detail.high': 'Respuestas completas y detalladas',

    // Message roles
    'message.role.user': 'Tú',
    'message.role.assistant': 'Asistente'
  },
  fr: {
    // French translations
    'chatbot.title': 'Assistant du manuel d\'IA Physique',
    'chatbot.newChat': 'Nouvelle Discussion',
    'chatbot.preferences': 'Préférences',
    'chatbot.export': 'Exporter',
    'chatbot.clear': 'Effacer la Conversation',
    'chatbot.welcome': 'Bonjour ! Je suis votre assistant pour le manuel d\'IA Physique.',
    'chatbot.welcome.desc': 'Posez-moi des questions sur les concepts d\'IA Physique et je vous fournirai des réponses basées sur le contenu du manuel avec les citations appropriées.',
    'chatbot.placeholder': 'Posez une question sur les concepts d\'IA Physique...',
    'chatbot.send': 'Envoyer',

    // Preferences
    'preferences.title': 'Préférences',
    'preferences.detailLevel': 'Niveau de Détail:',
    'preferences.detailLevel.concise': 'Concis',
    'preferences.detailLevel.balanced': 'Équilibré',
    'preferences.detailLevel.detailed': 'Détaillé',
    'preferences.responseFormat': 'Format de Réponse:',
    'preferences.responseFormat.paragraph': 'Paragraphe',
    'preferences.responseFormat.bullet': 'Points',
    'preferences.responseFormat.structured': 'Structuré',

    // Citations
    'citations.title': 'Sources:',
    'citations.relevance': 'Pertinence:',
    'citations.confidence': 'Confiance:',
    'citations.page': 'Page:',

    // Follow-up suggestions
    'followup.title': 'Questions suggérées:',

    // Loading states
    'loading.thinking': 'Réflexion...',

    // Error messages
    'error.session': 'Session expirée. Démarrage d\'une nouvelle conversation.',
    'error.response': 'Désolé, j\'ai rencontré une erreur en traitant votre question. Veuillez réessayer.',
    'error.noExport': 'Aucun historique de conversation à exporter.',

    // Keyboard shortcuts
    'shortcuts.info': 'Raccourcis clavier : Ctrl/Cmd+K pour le focus, Ctrl/Cmd+L pour effacer, Alt+P pour préférences, Alt+E pour exporter',

    // Accessibility
    'accessibility.chatLabel': 'Interface du Chatbot IA',
    'accessibility.messagesLabel': 'Conversation de chat',
    'accessibility.inputLabel': 'Saisie de message',
    'accessibility.sendButton': 'Envoyer le message',
    'accessibility.preferencesButton': 'Ouvrir les préférences',
    'accessibility.exportButton': 'Exporter la conversation',
    'accessibility.clearButton': 'Effacer la conversation',

    // Export
    'export.filename': 'chatbot-conversation',

    // Detail level descriptions
    'detail.low': 'Réponses brèves et concises',
    'detail.medium': 'Niveau équilibré de détail',
    'detail.high': 'Réponses complètes et détaillées',

    // Message roles
    'message.role.user': 'Vous',
    'message.role.assistant': 'Assistant'
  }
};

/**
 * Get translation for a given key and language
 * @param {string} key - The translation key
 * @param {string} language - The language code (default: 'en')
 * @param {Object} params - Optional parameters for interpolation
 * @returns {string} The translated string
 */
export const t = (key, language = DEFAULT_LANGUAGE, params = {}) => {
  const lang = SUPPORTED_LANGUAGES.includes(language) ? language : DEFAULT_LANGUAGE;
  const translation = TRANSLATIONS[lang]?.[key] || TRANSLATIONS[DEFAULT_LANGUAGE][key] || key;

  // Simple interpolation for parameters
  let result = translation;
  Object.keys(params).forEach(param => {
    result = result.replace(`{{${param}}}`, params[param]);
  });

  return result;
};

/**
 * Get all available languages
 * @returns {Array<string>} Array of supported language codes
 */
export const getSupportedLanguages = () => {
  return [...SUPPORTED_LANGUAGES];
};

/**
 * Check if a language is supported
 * @param {string} language - The language code to check
 * @returns {boolean} True if language is supported, false otherwise
 */
export const isLanguageSupported = (language) => {
  return SUPPORTED_LANGUAGES.includes(language);
};

/**
 * Get the direction of a language (ltr or rtl)
 * @param {string} language - The language code
 * @returns {string} 'ltr' for left-to-right, 'rtl' for right-to-left
 */
export const getLanguageDirection = (language) => {
  // For now, all supported languages are left-to-right
  // This can be extended as needed
  return 'ltr';
};

/**
 * Get language name in its native form
 * @param {string} language - The language code
 * @returns {string} The native name of the language
 */
export const getLanguageNativeName = (language) => {
  const names = {
    en: 'English',
    es: 'Español',
    fr: 'Français',
    de: 'Deutsch',
    zh: '中文',
    ja: '日本語'
  };

  return names[language] || language;
};

/**
 * Get language name in English
 * @param {string} language - The language code
 * @returns {string} The English name of the language
 */
export const getLanguageEnglishName = (language) => {
  const names = {
    en: 'English',
    es: 'Spanish',
    fr: 'French',
    de: 'German',
    zh: 'Chinese',
    ja: 'Japanese'
  };

  return names[language] || language;
};

// Note: React needs to be imported in the component that uses this context
// Context for React components
export const I18nContext = (typeof React !== 'undefined' && React.createContext) ?
  React.createContext({
    language: DEFAULT_LANGUAGE,
    setLanguage: () => {},
    t: (key, params) => t(key, DEFAULT_LANGUAGE, params),
    direction: 'ltr'
  }) : null;