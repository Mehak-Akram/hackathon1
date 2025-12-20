import React, { useState, useEffect } from 'react';
import OriginalLayout from '@theme-original/Layout';
import Chatbot from '../components/Chatbot/Chatbot';

/**
 * Custom Layout wrapper that adds the Chatbot to all pages
 */
export default function Layout(props) {
  const [showChatbot, setShowChatbot] = useState(false);

  // Listen for the openChatbot event dispatched from the navbar
  useEffect(() => {
    const handleOpenChatbot = () => {
      console.log('openChatbot event received, toggling chatbot visibility');
      setShowChatbot(prev => !prev); // Toggle visibility
    };

    // Add event listener
    document.addEventListener('openChatbot', handleOpenChatbot);

    // Test that the event listener is registered
    console.log('Event listener registered for openChatbot event in Layout wrapper');

    // Cleanup event listener on component unmount
    return () => {
      document.removeEventListener('openChatbot', handleOpenChatbot);
      console.log('Event listener removed for openChatbot event in Layout wrapper');
    };
  }, []);

  return (
    <>
      <OriginalLayout {...props} />
      {/* Conditionally render the Chatbot component */}
      {showChatbot && (
        <div
          className="chatbot-overlay"
          style={{
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            zIndex: 1000,
          }}
        >
          <Chatbot />
        </div>
      )}
    </>
  );
}