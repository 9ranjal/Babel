import React, { createContext, useContext } from 'react';
import { useChatSessions } from './useChatSessions';

type ChatSessionsValue = ReturnType<typeof useChatSessions>;

const ChatSessionsContext = createContext<ChatSessionsValue | null>(null);

export const ChatSessionsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const value = useChatSessions();
  return (
    <ChatSessionsContext.Provider value={value}>
      {children}
    </ChatSessionsContext.Provider>
  );
};

export const useChatSessionsContext = () => {
  const ctx = useContext(ChatSessionsContext);
  if (!ctx) {
    throw new Error('useChatSessionsContext must be used within a ChatSessionsProvider');
  }
  return ctx;
};








