import React, { createContext, useContext, useState, useEffect } from 'react';
import { getSupportedLanguages, isLanguageSupported, getLanguageDirection, t as translate } from './i18n';

const I18nContext = createContext({
  language: 'en',
  setLanguage: () => {},
  t: (key, params) => translate(key, 'en', params),
  direction: 'ltr'
});

/**
 * Language Provider component to wrap the chatbot with i18n capabilities
 */
export const LanguageProvider = ({ children, initialLanguage = 'en' }) => {
  const [language, setLanguage] = useState(() => {
    // Try to get language from localStorage first
    const savedLanguage = localStorage.getItem('chatbot-language');
    if (savedLanguage && isLanguageSupported(savedLanguage)) {
      return savedLanguage;
    }

    // Try to get from browser preferences
    const browserLang = navigator.language.split('-')[0];
    if (isLanguageSupported(browserLang)) {
      return browserLang;
    }

    // Fallback to initial language or default
    return isLanguageSupported(initialLanguage) ? initialLanguage : 'en';
  });

  const direction = getLanguageDirection(language);

  // Update language when it changes
  useEffect(() => {
    localStorage.setItem('chatbot-language', language);

    // Update document direction
    document.documentElement.lang = language;
    document.documentElement.dir = direction;
  }, [language, direction]);

  const value = {
    language,
    setLanguage,
    t: (key, params) => translate(key, language, params),
    direction
  };

  return (
    <I18nContext.Provider value={value}>
      {children}
    </I18nContext.Provider>
  );
};

/**
 * Custom hook to use the i18n context
 */
export const useI18n = () => {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error('useI18n must be used within a LanguageProvider');
  }
  return context;
};

export default LanguageProvider;