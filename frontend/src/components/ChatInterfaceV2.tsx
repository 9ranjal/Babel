import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { RotateCcw, ChevronDown } from 'lucide-react';
import MarkdownRenderer from './MarkdownRenderer';
import CitationCard from './CitationCard';
import { useChatSessions } from '../hooks/useChatSessions';
import { parseSSE } from '../lib/sse';

interface ChatInterfaceV2Props {
  module?: 'quiz' | 'notes' | 'flashcards' | 'search' | 'learn';
  isMain?: boolean;
  contextData?: any;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp?: Date;
  quoteTitle?: string;
  quoteText?: string;
  tutorResponse?: {
    answer?: string;
    citations?: any[];
    questions_next?: Array<{ prompt: string; type?: string }>;
  };
}

// Note embed block
const NoteEmbedBlock: React.FC<{ title: string | null; text: string; onDismiss: () => void }> = ({ title, text, onDismiss }) => (
  <motion.div
    initial={{ opacity: 0, y: -12, scale: 0.95 }}
    animate={{ opacity: 1, y: 0, scale: 1 }}
    exit={{ opacity: 0, y: -8, scale: 0.95 }}
    transition={{ duration: 0.3 }}
    className="mb-3 p-3 bg-[#F0E68C] rounded-lg border-2 border-[#F0E68C] relative w-full max-w-full"
  >
    <div className="absolute left-0 top-0 bottom-0 w-1.5 bg-[#F0E68C] rounded-l-lg" />
    <div className="pl-2">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-[#1f2328] font-semibold">✨ {title || 'Embedded Text'}</span>
        <button
          type="button"
          className="p-1 text-[#1f2328] hover:text-[#3b3b3b] rounded transition-colors"
          onClick={onDismiss}
        >
          <ChevronDown className="w-4 h-4" />
        </button>
      </div>
      <div className="text-sm text-[#1f2328] whitespace-pre-wrap italic max-h-32 overflow-y-auto">
        {text}
      </div>
    </div>
  </motion.div>
);

// Message Component
const Message: React.FC<{ 
  message: Message; 
  isLast: boolean; 
  earlyCitations?: any[];
  onQuestionSelect?: (question: string) => void;
}> = ({ message, earlyCitations = [], onQuestionSelect }) => {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === 'user';

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
    >
      <div className={`max-w-[95%] ${isUser ? 'order-2' : 'order-1'}`}>
        <div className={`flex items-start ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
          <div className={`flex-1 ${isUser ? 'text-right' : 'text-left'}`}>
            <div className={`inline-block p-4 rounded-2xl break-words ${
              isUser
                ? 'bg-[#f0ede0] text-[#2b2c28]'
                : 'bg-white/70 text-[#2b2c28] backdrop-blur-sm border border-[#e9e4d3]/60'
            }`}>
              {isUser ? (
                <div className="whitespace-pre-wrap text-left">
                  {message.quoteText && (
                    <div className="mb-2 p-3 border border-[#d9d4c4]/30 rounded-md bg-[#f0ede0]/10">
                      {message.quoteTitle && (
                        <div className="text-xs text-blue-300 mb-1 truncate">{message.quoteTitle}</div>
                      )}
                      <div className="text-sm text-neutral-200 whitespace-pre-wrap italic">{message.quoteText}</div>
                    </div>
                  )}
                  <div>{message.content}</div>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="prose max-w-none break-words overflow-wrap-anywhere text-[#2b2c28]">
                    <MarkdownRenderer 
                      content={message.content || ''}
                      citations={message.tutorResponse?.citations || earlyCitations || []}
                    />
                  </div>
                  
                  <AnimatePresence mode="wait">
                    {message.tutorResponse?.citations && message.tutorResponse.citations.length > 0 && (
                      <motion.div 
                        initial={{ opacity: 0, height: 0, marginTop: 0 }}
                        animate={{ opacity: 1, height: "auto", marginTop: 12 }}
                        exit={{ opacity: 0, height: 0, marginTop: 0 }}
                        transition={{ duration: 0.4, ease: [0.4, 0, 0.2, 1] }}
                        className="rounded-lg p-3 bg-[#f0ede0]/30 border border-[#d9d4c4]/40 overflow-hidden"
                      >
                        <div className="grid grid-cols-1 gap-2">
                          {message.tutorResponse.citations.map((citation: any, index: number) => (
                            <motion.div
                              key={index}
                              initial={{ opacity: 0, scale: 0.95 }}
                              animate={{ opacity: 1, scale: 1 }}
                              transition={{ duration: 0.3, delay: 0.1 + index * 0.05 }}
                            >
                              <CitationCard citation={citation} index={index} />
                            </motion.div>
                          ))}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              )}
            </div>

            {!isUser && (
              <div className="flex items-center gap-2 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={handleCopy}
                  className="text-xs text-zinc-500 hover:text-zinc-300 transition-colors px-2 py-1 rounded"
                >
                  {copied ? 'Copied!' : 'Copy'}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
};

// Suggested Questions Bubble
const SuggestedQuestionsBubble: React.FC<{ 
  tutorResponse: any; 
  onQuestionSelect?: (question: string) => void;
}> = ({ tutorResponse, onQuestionSelect }) => {
  if (!tutorResponse || !tutorResponse.questions_next || tutorResponse.questions_next.length === 0) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: "auto" }}
      exit={{ opacity: 0, height: 0 }}
      transition={{ duration: 0.4, ease: [0.4, 0, 0.2, 1] }}
      className="flex justify-start mb-1 mt-0 overflow-hidden"
    >
      <div className="flex items-start">
        <div className="flex-1">
          <div className="inline-block p-4 rounded-2xl bg-gray-200/90 border border-gray-300/60">
            <div className="text-gray-800 mb-3 flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              Follow-up Questions
            </div>
            <div className="flex flex-wrap gap-2">
              {tutorResponse.questions_next.map((question: any, index: number) => (
                <motion.button
                  key={index}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.3, delay: 0.1 + index * 0.05 }}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => onQuestionSelect?.(question.prompt)}
                  className="group relative backdrop-blur-md border rounded-2xl px-4 py-2 transition-all duration-200 text-sm text-gray-900 bg-gray-100/80 hover:bg-gray-100 border-gray-300/60"
                >
                  <span className="font-mono text-xs text-gray-600 mr-2">{question.type || 'check'}</span>
                  <span className="text-gray-900">{question.prompt}</span>
                </motion.button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default function ChatInterfaceV2({ module = 'search', isMain = true, contextData }: ChatInterfaceV2Props) {
  const isMainView = isMain;
  const chatSessions = useChatSessions();
  const { currentSession, addMessage, createSession } = isMainView ? chatSessions : { 
    currentSession: null, 
    addMessage: () => {}, 
    createSession: () => '' 
  };

  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState<string>('');
  const [currentPhase, setCurrentPhase] = useState<string | null>(null);
  const [phaseMeta, setPhaseMeta] = useState<any | null>(null);
  const [planningPreview, setPlanningPreview] = useState<string[]>([]);
  const [currentLineIndex, setCurrentLineIndex] = useState<number>(0);
  const [isGeneratingFollowups, setIsGeneratingFollowups] = useState<boolean>(false);
  const [earlyCitations, setEarlyCitations] = useState<any[]>([]);
  const [embeddedText, setEmbeddedText] = useState<string | null>(null);
  const [embeddedTitle, setEmbeddedTitle] = useState<string | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const processingMessageRef = useRef<boolean>(false);

  // Create session on mount if needed
  useEffect(() => {
    if (isMainView && !currentSession) {
      createSession('New conversation', module);
    }
  }, [isMainView, currentSession, createSession, module]);

  // Auto-scroll - only when there are messages and not on initial load
  const prevMessagesLengthRef = useRef<number>(0);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const hasScrolledRef = useRef<boolean>(false);
  
  useEffect(() => {
    const currentMessagesLength = currentSession?.messages?.length || 0;
    // Only scroll if messages exist and we've added new messages (not initial load)
    if (currentMessagesLength > 0 && currentMessagesLength !== prevMessagesLengthRef.current) {
      // Small delay to ensure DOM is updated
      setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        hasScrolledRef.current = true;
      }, 100);
    }
    prevMessagesLengthRef.current = currentMessagesLength;
  }, [currentSession?.messages, isLoading]);

  // Ensure scroll position is at top on initial load or when switching sessions
  useEffect(() => {
    hasScrolledRef.current = false;
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = 0;
    }
  }, [currentSession?.id]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  // Cycle through planning preview lines for single-line display
  useEffect(() => {
    if (planningPreview.length <= 1) {
      setCurrentLineIndex(0);
      return;
    }
    const interval = setInterval(() => {
      setCurrentLineIndex(prev => (prev + 1) % planningPreview.length);
    }, 2000);
    return () => clearInterval(interval);
  }, [planningPreview.length]);

  // (Removed) Command suggestions feature

  const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:5002';

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isLoading || processingMessageRef.current) return;
    
    processingMessageRef.current = true;
    setIsLoading(true);

    if (isMainView && currentSession) {
      addMessage(currentSession.id, {
        role: 'user',
        content: content.trim()
      });
    }

    setInput('');
    setStreamingMessage('');
    setEarlyCitations([]);

    try {
      const requestBody = {
        input: content,
        module: module,
        contextData: contextData || null,
        tutorMode: 'chat',
        chat_history: (currentSession?.messages || []).slice(-10).map(msg => ({
          sender: msg.role || 'user',
          content: msg.content || '',
          timestamp: msg.timestamp || new Date().toISOString()
        })),
      };

      const response = await fetch(`${API_BASE}/api/copilot/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      let accumulatedContent = '';
      let citationsReceived = false;

      for await (const evt of parseSSE(response)) {
        const type = (evt as any).type;
        
        if (type === 'phase') {
          const phase = (evt as any).phase as string | undefined;
          const meta = (evt as any).meta as any | undefined;
          setCurrentPhase(phase || null);
          setPhaseMeta(meta || null);
          if (phase === 'followups') setIsGeneratingFollowups(true);
          if (phase === 'followups_ready') setIsGeneratingFollowups(false);
          if (phase === 'planning_ready' && meta?.bullets && Array.isArray(meta.bullets)) {
            setPlanningPreview((meta.bullets as string[]).slice(0, 5));
          }
          if (phase === 'drafting' && planningPreview.length > 0) {
            // keep preview visible briefly while drafting; do not clear here
          }
        }
        
        if (type === 'citations_ready' && (evt as any).citations) {
          setEarlyCitations((evt as any).citations);
          citationsReceived = true;
        }
        
        if (type === 'chunk' && (evt as any).chunk) {
          accumulatedContent += (evt as any).chunk;
          setStreamingMessage(accumulatedContent);
        } else if (type === 'tutor_response') {
          const tutorData = (evt as any).data;
          const finalContent = accumulatedContent || tutorData?.answer || '';
          
          if (isMainView && currentSession) {
            addMessage(currentSession.id, {
              role: 'assistant',
              content: finalContent,
              tutorResponse: tutorData
            });
          }
          
          setStreamingMessage('');
          setIsLoading(false);
          setCurrentPhase(null);
          setPhaseMeta(null);
          setPlanningPreview([]);
          setIsGeneratingFollowups(false);
          processingMessageRef.current = false;
          break;
        } else if (type === 'error') {
          const errMsg = (evt as any).error || 'Unknown error';
          if (isMainView && currentSession) {
            addMessage(currentSession.id, {
              role: 'assistant',
              content: `❌ Error: ${errMsg}`
            });
          }
          setStreamingMessage('');
          setIsLoading(false);
          setPhaseMeta(null);
          setPlanningPreview([]);
          setIsGeneratingFollowups(false);
          processingMessageRef.current = false;
          break;
        }
      }
    } catch (err) {
      console.error('Chat error:', err);
      const errorMessage = err instanceof Error ? err.message : 'An unexpected error occurred';
      if (isMainView && currentSession) {
        addMessage(currentSession.id, {
          role: 'assistant',
          content: `❌ Error: ${errorMessage}`
        });
      }
      setStreamingMessage('');
      setIsLoading(false);
      processingMessageRef.current = false;
    }
  }, [currentSession, addMessage, module, contextData, isLoading, API_BASE, isMainView]);

  const handleFollowUpQuestion = useCallback((question: string) => {
    if (!isLoading) {
      sendMessage(question);
    }
  }, [sendMessage, isLoading]);

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const prefix = embeddedText ? `> ${embeddedText.replace(/\n/g, '\n> ')}\n\n` : '';
    const fullInput = (prefix + input.trim()).trim();
    sendMessage(fullInput);
    setEmbeddedText(null);
    setEmbeddedTitle(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleFormSubmit(e as any);
    }
  };

  // Rotating welcome prompts (subtitle under the welcome line)
  const welcomePrompts = [
    'Consensus as a Service',
    'Bridge Terms',
    'Decipher the Jargon',
    'Negotiate with Confidence',
    'Term Sheet Intelligence',
    'BATNA-Driven Advice'
  ];
  const [subtitleIndex, setSubtitleIndex] = useState(0);
  const [welcomeSubtitle, setWelcomeSubtitle] = useState<string>(welcomePrompts[0]);
  
  // Cycle through subtitles with smooth transitions
  useEffect(() => {
    if (!isMain) return;
    
    const interval = setInterval(() => {
      setSubtitleIndex((prev) => (prev + 1) % welcomePrompts.length);
    }, 3000); // Change every 3 seconds
    
    return () => clearInterval(interval);
  }, [isMain, welcomePrompts.length]);

  // Update subtitle when index changes
  useEffect(() => {
    setWelcomeSubtitle(welcomePrompts[subtitleIndex]);
  }, [subtitleIndex]);

  const messages = currentSession?.messages || [];
  const isEmptyState = (messages.length === 0) && !streamingMessage;

  return (
    <div className="flex flex-col h-full relative copilot-ambient-bg">
      {/* Messages Area */}
      <div ref={messagesContainerRef} className="flex-1 overflow-y-auto px-4 pb-3 min-h-0 flex flex-col">
        <div className="w-full max-w-4xl mx-auto flex flex-col" style={{ minHeight: '100%' }}>
        {/* New Chat control */}
        {messages.length > 0 && (
          <div className="flex justify-center gap-2 pt-3 pb-1.5">
            <button
              onClick={() => createSession('New conversation', module)}
              className="px-4 py-2 text-sm bg-[#f0ede0] hover:bg-[#d9d4c4] text-[#2b2c28] rounded-lg transition-colors border border-[#d9d4c4]/30"
            >
              + New Chat
            </button>
          </div>
        )}
        {messages.length === 0 ? (
          <div className="flex flex-col items-center text-center relative" style={{ paddingTop: 'calc((100vh - 40px) * 0.3 - 115px)' }}>
            <div className="w-full max-w-4xl mx-auto">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="mb-3"
              >
                <div className="mb-2.5 flex justify-center">
                  <motion.img 
                    src="/babel-logo.svg" 
                    alt="Babel Logo" 
                    className="w-32 h-32 md:w-36 md:h-36"
                    style={{ maxWidth: '144px', maxHeight: '144px' }}
                    animate={{
                      scale: [1, 1.02, 1],
                    }}
                    transition={{
                      duration: 4,
                      repeat: Infinity,
                      ease: "easeInOut"
                    }}
                  />
                </div>
                <h1 className="text-2xl md:text-3xl font-bold mb-1" style={{ color: '#0E0F14' }}>
                  Welcome to Babel
                </h1>
                <div className="relative h-7 md:h-8">
                  <AnimatePresence mode="wait">
                    <motion.p
                      key={subtitleIndex}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -8 }}
                      transition={{ duration: 0.6, ease: "easeInOut" }}
                      className="text-sm md:text-base max-w-md mx-auto leading-relaxed absolute inset-0 flex items-center justify-center"
                      style={{ color: '#5A6066', opacity: 0.8 }}
                    >
                      {welcomeSubtitle}
                    </motion.p>
                  </AnimatePresence>
                </div>
              </motion.div>
              {/* Empty-state centered composer */}
              {isEmptyState && (
                <div className="px-4 pb-3 mt-3">
                  <div className="relative max-w-4xl mx-auto">
                    <form onSubmit={handleFormSubmit} className="w-full">
                      <AnimatePresence>
                        {embeddedText && (
                          <NoteEmbedBlock
                            title={embeddedTitle || 'Selected Text'}
                            text={embeddedText}
                            onDismiss={() => {
                              setEmbeddedText(null);
                              setEmbeddedTitle(null);
                            }}
                          />
                        )}
                      </AnimatePresence>
                      
                      <div className={`relative min-h-[68px] transition-all duration-300 ease-out composer glow-edges ${input?.length ? 'has-value' : ''}`}>
                        <div className="flex items-center gap-3 px-5 py-4">
                          <span className="fake-caret" aria-hidden="true" />
                          <textarea
                            ref={textareaRef}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Message Babel..."
                            disabled={isLoading}
                            rows={3}
                            className="flex-1 bg-transparent resize-none outline-none border-none focus:outline-none focus:ring-0 focus:border-none disabled:opacity-50 disabled:cursor-not-allowed min-h-[48px] max-h-[260px] leading-[26px] text-[16px]"
                            style={{ height: 'auto' }}
                          />
                          <div className="flex items-center gap-2">
                            <button
                              type="submit"
                              disabled={!input.trim() || isLoading}
                              className="bg-[color:var(--ink-900)] hover:bg-[#1f201a] disabled:bg-[#a1a1a1] disabled:cursor-not-allowed text-white p-2 rounded-md transition-colors shadow-sm"
                            >
                              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                              </svg>
                            </button>
                          </div>
                        </div>
                      </div>
                    </form>
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="space-y-3 w-full pt-3">
            {messages.map((message, index) => (
              <React.Fragment key={message.id}>
                <Message 
                  message={message} 
                  isLast={index === messages.length - 1}
                  earlyCitations={earlyCitations}
                  onQuestionSelect={handleFollowUpQuestion}
                />
                
                {message.role === 'assistant' && (message as any).tutorResponse && (
                  <SuggestedQuestionsBubble
                    tutorResponse={(message as any).tutorResponse}
                    onQuestionSelect={handleFollowUpQuestion}
                  />
                )}
              </React.Fragment>
            ))}
          </div>
        )}

        {/* Streaming Message */}
        {streamingMessage && (
          <Message 
            earlyCitations={earlyCitations}
            message={{
              id: 'streaming',
              role: 'assistant',
              content: streamingMessage,
              timestamp: new Date()
            }}
            isLast={true}
            onQuestionSelect={handleFollowUpQuestion} 
          />
        )}

      {/* Thinking Mode */}
      {isLoading && !streamingMessage && (
          <div className="flex justify-start mb-4">
            <div className="inline-flex items-start gap-3 px-4 py-3 rounded-2xl bg-[#f0ede0] text-[#1f2328] border border-[#d9d4c4]">
              <div className="flex items-center gap-2 text-sm font-medium">
                <span>
                  {currentPhase === 'planning' && 'Planning'}
                {currentPhase === 'pib_fetch' && 'Fetching PIB Articles'}
                {currentPhase === 'pib_classify' && 'Categorizing Articles'}
                {currentPhase === 'pib_summarize' && 'Generating Summary'}
                  {currentPhase === 'drafting' && 'Drafting'}
                  {currentPhase === 'critique' && 'Critiquing'}
                {isGeneratingFollowups && 'Generating Follow-ups'}
                {!currentPhase && !isGeneratingFollowups && 'Thinking'}
                </span>
                <span className="inline-flex items-center gap-1">
                  <motion.span
                    animate={{ opacity: [0.3, 1, 0.3] }}
                    transition={{ duration: 1.2, repeat: Infinity, ease: 'easeInOut' }}
                    className="w-2 h-2 rounded-full bg-[#1f2328]"
                  />
                  <motion.span
                    animate={{ opacity: [0.3, 1, 0.3] }}
                    transition={{ duration: 1.2, repeat: Infinity, ease: 'easeInOut', delay: 0.2 }}
                    className="w-2 h-2 rounded-full bg-[#1f2328]"
                  />
                  <motion.span
                    animate={{ opacity: [0.3, 1, 0.3] }}
                    transition={{ duration: 1.2, repeat: Infinity, ease: 'easeInOut', delay: 0.4 }}
                    className="w-2 h-2 rounded-full bg-[#1f2328]"
                  />
                </span>
              </div>
            {/* Details line */}
            {currentPhase && phaseMeta && (
              <div className="ml-2 text-[12px] leading-snug opacity-80">
                {(() => {
                  const lines: string[] = [];
                  const titleCase = (s?: string) => (s ? s.replace(/(^|_|-)([a-z])/g, (_: string, __: string, p2: string) => ' ' + p2.toUpperCase()).trim() : undefined);
                  if (currentPhase === 'planning') {
                    if (phaseMeta.resolved_referent) lines.push(`Continuing about "${phaseMeta.resolved_referent}"`);
                    const d = titleCase(phaseMeta.domain); if (d) lines.push(`Analyzing as ${d} question`);
                    if (Array.isArray(phaseMeta.bullets) && phaseMeta.bullets.length) {
                      lines.push(`Analyzing: ${phaseMeta.bullets[0]}`);
                    }
                  } else if (currentPhase === 'drafting') {
                    if (typeof phaseMeta.bullets === 'number') lines.push(`Writing with ${phaseMeta.bullets} key points`);
                  } else if (currentPhase === 'critique') {
                    lines.push('Reviewing for quality');
                  }
                  if (isGeneratingFollowups) lines.push('Generating follow-up questions');
                  const currentLine = lines[currentLineIndex % Math.max(1, lines.length)];
                  return currentLine ? (
                    <motion.div
                      key={currentLineIndex}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      transition={{ duration: 0.3 }}
                    >
                      {currentLine}
                    </motion.div>
                  ) : null;
                })()}
              </div>
            )}
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area - Bottom composer only when chat has started */}
      {!isEmptyState && (
        <div className="p-4 sidebar-gradient">
          <form onSubmit={handleFormSubmit} className="w-full max-w-4xl mx-auto">
            <AnimatePresence>
              {embeddedText && (
                <NoteEmbedBlock
                  title={embeddedTitle || 'Selected Text'}
                  text={embeddedText}
                  onDismiss={() => {
                    setEmbeddedText(null);
                    setEmbeddedTitle(null);
                  }}
                />
              )}
            </AnimatePresence>
            
            <div className={`relative min-h-[44px] transition-all duration-300 ease-out overflow-hidden composer focus-within:shadow-none`}>
              <div className="flex items-center gap-3 p-3">
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Message Babel..."
                  disabled={isLoading}
                  rows={1}
                  className="flex-1 bg-transparent resize-none outline-none border-none focus:outline-none focus:ring-0 focus:border-none disabled:opacity-50 disabled:cursor-not-allowed min-h-[20px] max-h-[200px] leading-[20px]"
                  style={{ height: 'auto' }}
                />
                <div className="flex items-center gap-2">
                  <button
                    type="submit"
                    disabled={!input.trim() || isLoading}
                    className="bg-[color:var(--ink-900)] hover:bg-[#1f201a] disabled:bg-[#a1a1a1] disabled:cursor-not-allowed text-white p-2 rounded-md transition-colors shadow-sm"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

