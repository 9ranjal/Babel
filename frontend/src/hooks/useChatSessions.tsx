import { useState, useEffect, useCallback, useMemo, useRef } from 'react';

export interface ChatSession {
  id: string;
  title: string;
  timestamp: Date;
  messageCount: number;
  module: string;
  messages: ChatMessage[];
  documentId?: string; // associated uploaded document id (for graph/viewer)
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  tutorResponse?: any;
}

const STORAGE_KEY = 'babel-chat-sessions';

// Load sessions from localStorage
const loadSessions = (): ChatSession[] => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      return parsed.map((session: any) => ({
        ...session,
        timestamp: new Date(session.timestamp),
        messages: (session.messages || []).map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        }))
      }));
    }
  } catch (error) {
    console.error('Error loading chat sessions:', error);
  }
  return [];
};

// Save sessions to localStorage
const saveSessions = (sessions: ChatSession[]) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
  } catch (error) {
    console.error('Error saving chat sessions:', error);
  }
};

export function useChatSessions() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load sessions on mount
  useEffect(() => {
    setIsLoading(true);
    const loaded = loadSessions();
    setSessions(loaded);
    if (loaded.length > 0) {
      setCurrentSessionId(loaded[0].id);
    }
    setIsLoading(false);
  }, []);

  // Save sessions whenever they change
  useEffect(() => {
    if (sessions.length > 0) {
      saveSessions(sessions);
    }
  }, [sessions]);

  const createSession = useCallback((title = 'New conversation', module = 'search'): string => {
    const newSession: ChatSession = {
      id: Date.now().toString(),
      title,
      timestamp: new Date(),
      messageCount: 0,
      module,
      messages: []
    };
    
    setSessions(prev => {
      const updated = [newSession, ...prev];
      return updated;
    });
    
    setCurrentSessionId(newSession.id);
    return newSession.id;
  }, []);

  const selectSession = useCallback((sessionId: string) => {
    setCurrentSessionId(sessionId);
  }, []);

  const deleteSession = useCallback((sessionId: string) => {
    setSessions(prev => {
      const updated = prev.filter(session => session.id !== sessionId);
      if (currentSessionId === sessionId) {
        setCurrentSessionId(updated.length > 0 ? updated[0].id : null);
      }
      return updated;
    });
  }, [currentSessionId]);

  const addMessage = useCallback((sessionId: string, message: Omit<ChatMessage, 'id' | 'timestamp'>) => {
    const newMessage: ChatMessage = {
      ...message,
      id: crypto.randomUUID(),
      timestamp: new Date()
    };

    setSessions(prev => {
      return prev.map(session => {
        if (session.id === sessionId) {
          const updatedMessages = [...session.messages, newMessage];
          let updatedTitle = session.title;
          if (session.messages.length === 0 && message.role === 'user') {
            updatedTitle = message.content.slice(0, 50) + (message.content.length > 50 ? '...' : '');
          }
          
          return {
            ...session,
            messages: updatedMessages,
            messageCount: updatedMessages.length,
            title: updatedTitle
          };
        }
        return session;
      });
    });
  }, []);

  const attachDocument = useCallback((sessionId: string, documentId: string) => {
    setSessions(prev => {
      return prev.map(session => {
        if (session.id === sessionId) {
          return { ...session, documentId };
        }
        return session;
      });
    });
  }, []);

  const currentSession = useMemo(() => {
    return sessions.find(session => session.id === currentSessionId) || null;
  }, [sessions, currentSessionId]);

  const syncToSupabase = useCallback(async () => {
    // Placeholder for future Supabase sync
    console.log('Sync to Supabase (not implemented)');
  }, []);

  const hydrateFromSupabase = useCallback(async () => {
    // Placeholder for future Supabase hydration
    console.log('Hydrate from Supabase (not implemented)');
  }, []);

  const createFreshSession = useCallback((title = 'New conversation', module = 'search'): string => {
    return createSession(title, module);
  }, [createSession]);

  const updateSessionTitle = useCallback((sessionId: string, newTitle: string) => {
    setSessions(prev => {
      return prev.map(session => {
        if (session.id === sessionId) {
          return {
            ...session,
            title: newTitle
          };
        }
        return session;
      });
    });
  }, []);

  return {
    sessions,
    currentSession,
    currentSessionId,
    isLoading,
    createSession,
    createFreshSession,
    selectSession,
    deleteSession,
    updateSessionTitle,
    addMessage,
    attachDocument,
    syncToSupabase,
    hydrateFromSupabase,
  };
}

