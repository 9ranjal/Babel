import { useState, useRef, useCallback } from 'react';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  quoteTitle?: string;
  quoteText?: string;
  tutorResponse?: any;
}

export interface UseStreamingChatOptions {
  api: string;
  body?: Record<string, any>;
  onError?: (error: Error) => void;
  onFinish?: (message: ChatMessage) => void;
}

export function useStreamingChat(options: UseStreamingChatOptions) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  
  const abortControllerRef = useRef<AbortController | null>(null);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
  }, []);

  const sendMessage = useCallback(async (content: string, meta?: { quoteTitle?: string; quoteText?: string }) => {
    if (!content.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
      quoteTitle: meta?.quoteTitle,
      quoteText: meta?.quoteText,
    };

    const assistantMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage, assistantMessage]);
    setIsLoading(true);
    setError(null);
    setInput('');

    abortControllerRef.current?.abort();
    abortControllerRef.current = new AbortController();

    const requestBody = {
      ...options.body,
      input: content,
      chat_history: messages.slice(-10).map(msg => ({
        sender: msg.role,
        content: msg.content,
        timestamp: msg.timestamp
      })),
    };

    try {
      const timeoutId = setTimeout(() => {
        abortControllerRef.current?.abort();
      }, 60000);
      
      const response = await fetch(options.api, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(requestBody),
        signal: abortControllerRef.current.signal,
      });
      
      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const { parseSSE } = await import('../lib/sse');
      let accumulatedContent = '';
      
      for await (const evt of parseSSE(response)) {
        const type = (evt as any).type;
        
        if (type === 'chunk' && (evt as any).chunk) {
          accumulatedContent += (evt as any).chunk;
          setMessages(prev => prev.map(msg =>
            msg.id === assistantMessage.id
              ? { ...msg, content: accumulatedContent }
              : msg
          ));
        } else if (type === 'tutor_response') {
          const tutorData = (evt as any).data;
          if (tutorData) {
            const finalContent = tutorData.answer || accumulatedContent || '';
            assistantMessage.content = finalContent;
            (assistantMessage as any).tutorResponse = tutorData;
            
            setMessages(prev => prev.map(m =>
              m.id === assistantMessage.id
                ? { 
                    ...m, 
                    content: finalContent,
                    tutorResponse: tutorData
                  }
                : m
            ));
          }
          if (options.onFinish) options.onFinish(assistantMessage);
          setIsLoading(false);
          break;
        } else if (type === 'error') {
          const errMsg = (evt as any).error || 'Unknown error';
          const err = new Error(String(errMsg));
          setError(err);
          setMessages(prev => prev.map(m =>
            m.id === assistantMessage.id
              ? { ...m, content: `❌ Error: ${errMsg}` }
              : m
          ));
          if (options.onError) options.onError(err);
          setIsLoading(false);
          break;
        }
      }

      if (isLoading) setIsLoading(false);
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        return;
      }
      
      const error = err instanceof Error ? err : new Error('Unknown error');
      setError(error);
      setIsLoading(false);
      
      if (options.onError) {
        options.onError(error);
      }
    }
  }, [messages, isLoading, options]);

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    sendMessage(input);
  }, [input, isLoading, sendMessage]);

  const reload = useCallback(() => {
    if (messages.length > 0) {
      const lastUserMessage = messages.findLast(msg => msg.role === 'user');
      if (lastUserMessage) {
        setMessages(prev => prev.filter(msg => msg.role === 'user' || msg.id !== lastUserMessage.id));
        sendMessage(lastUserMessage.content);
      }
    }
  }, [messages, sendMessage]);

  return {
    messages,
    input,
    handleInputChange,
    handleSubmit,
    sendMessage,
    isLoading,
    error,
    reload,
    setInput,
  };
}

