import { useEffect, useMemo, useRef, useState } from 'react';
import { Button } from './ui/Button';
import { Textarea } from './ui/Textarea';
import { Badge } from './ui/Badge';
import { Send, Wand2, MessageSquareText, Loader2, Building2, Upload as UploadIcon } from 'lucide-react';
import { api } from '../lib/apiClient';
import { upload as uploadDocument, getDocument, listClauses, getDocumentStatus } from '../lib/api';
import { useDocStore } from '../lib/store';
import { useToast } from '../hooks/useToast';
import type { Message, Transaction, CopilotResponse } from '../types';

interface MessageDisplayProps {
  msg: Message;
}

const MessageBubble = ({ msg }: MessageDisplayProps) => {
  const isAssistant = msg.role === 'assistant';
  
  return (
    <div className={`flex ${isAssistant ? 'justify-start' : 'justify-end'}`}>
      <div className={`max-w-[85%] rounded-lg px-4 py-3 text-sm leading-relaxed shadow-md transition-all ${
        isAssistant 
          ? 'bg-gradient-to-br from-zinc-50 to-zinc-100 text-zinc-900 border border-zinc-200' 
          : 'bg-gradient-to-br from-indigo-600 to-indigo-700 text-white'
      }`}>
        <div className="whitespace-pre-wrap">{msg.content}</div>
        {msg.termSheet && (
          <div className="mt-3 border-t pt-3">
            <div className="bg-white rounded-lg p-4 border shadow-sm">
              <h4 className="font-medium text-sm mb-2">Generated Term Sheet</h4>
              <div className="text-xs text-zinc-600 whitespace-pre-wrap max-h-40 overflow-y-auto">
                {msg.termSheet}
              </div>
            </div>
          </div>
        )}
        {msg.suggestion && (
          <div className="mt-2 flex items-center gap-2 text-xs">
            <Badge className="bg-indigo-100 text-indigo-700">Suggestion</Badge>
          </div>
        )}
      </div>
    </div>
  );
};

interface CopilotChatProps {
  onSuggestion?: (suggestion: any) => void;
  currentTransaction: Transaction | null;
  onTermSheetReady?: (data: any) => void;
}

export default function CopilotChat({ 
  onSuggestion, 
  currentTransaction,
  onTermSheetReady,
}: CopilotChatProps) {
  const [chat, setChat] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { showSuccess, showError } = useToast();
  const setDocId = useDocStore((s) => s.setDocId);
  const setDocument = useDocStore((s) => s.setDocument);
  const setClauses = useDocStore((s) => s.setClauses);
  const setSelected = useDocStore((s) => s.setSelected);
  const clearAnalyses = useDocStore((s) => s.clearAnalyses);

  const sessionId = useMemo(() => {
    return `session_${Date.now()}`;
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chat, loading]);

  const send = async () => {
    if (!input.trim()) return;
    
    const userMsg: Message = { 
      id: `u-${Date.now()}`, 
      role: 'user', 
      content: input.trim(), 
      ts: Date.now() 
    };
    
    setChat((c) => [...c, userMsg]);
    setInput('');
    setLoading(true);
    
    try {
      // Detect intent from user message
      const lower = userMsg.content.toLowerCase();
      let intent = 'general_chat';
      let endpoint = '/api/copilot/chat';
      
      if (lower.includes('explain') || lower.includes('what is') || lower.includes('tell me about')) {
        intent = 'explain_clause';
        endpoint = '/api/copilot/intent';
      } else if (lower.includes('change') || lower.includes('revise')) {
        intent = 'revise_clause';
        endpoint = '/api/copilot/intent';
      } else if (lower.includes('simulate') || lower.includes('trade')) {
        intent = 'simulate_trade';
        endpoint = '/api/copilot/intent';
      }
      
      const response = await api.post<CopilotResponse>(endpoint, {
        intent,
        session_id: sessionId,
        message: userMsg.content,
        acting_as: 'founder',
        transaction_id: currentTransaction?.id || null
      });
      
      const result = response.data;
      const aiMsg: Message = { 
        id: `a-${Date.now()}`, 
        ts: Date.now(), 
        role: 'assistant',
        content: result.message,
        suggestion: result.updated_clauses && result.updated_clauses.length > 0 ? {
          id: `s-${Date.now()}`,
          type: 'update',
          rationale: result.message
        } : null
      };
      
      setChat((c) => [...c, aiMsg]);
      if (aiMsg.suggestion && typeof onSuggestion === 'function') {
        onSuggestion(aiMsg.suggestion);
      }
    } catch (error: any) {
      console.error('Copilot API error:', error);
      const errorMsg: Message = { 
        id: `a-${Date.now()}`, 
        ts: Date.now(), 
        role: 'assistant',
        content: `Sorry, I encountered an error: ${error.message}. Please try again.`
      };
      setChat((c) => [...c, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const quickPrompts = useMemo(
    () => [
      { id: 'qp1', label: 'Explain Liquidation Pref', text: 'Explain liquidation preference and its implications for founders' },
      { id: 'qp2', label: 'Review Anti-Dilution', text: 'Review anti-dilution provisions and suggest founder-friendly alternatives' },
      { id: 'qp3', label: 'Board Composition', text: 'Analyze board composition and voting rights for founder protection' },
      { id: 'qp4', label: 'Simulate Trade', text: 'What if we trade liquidation preference for better board control?' },
    ],
    []
  );

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const triggerUpload = () => {
    if (uploading) return;
    fileInputRef.current?.click();
  };

  const handleFileSelected = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));
      const readyStatuses = new Set(['extracted', 'graphed', 'analyzed']);

      const { document_id, requeued } = await uploadDocument(file);
      setDocId(document_id);
      showSuccess('Upload started', requeued ? 'Queued parse job, waiting for worker…' : 'Parsing term sheet…');
      // Poll status until downstream stages complete (up to ~2 minutes)
      let status: string = 'uploaded';
      const statusDeadline = Date.now() + 120000; // allow full pipeline to complete
      while (Date.now() < statusDeadline) {
        try {
          const s = await getDocumentStatus(document_id);
          status = s.status;
          if (readyStatuses.has(status)) break;
        } catch {
          // ignore transient failures
        }
        await sleep(800);
      }
      const doc = await getDocument(document_id);
      status = doc?.status ?? status;
      let clauses = await listClauses(document_id);
      if (clauses.length === 0 && readyStatuses.has(status)) {
        const clausesDeadline = Date.now() + 20000;
        while (Date.now() < clausesDeadline) {
          await sleep(1000);
          clauses = await listClauses(document_id);
          if (clauses.length > 0) break;
        }
      }
      clearAnalyses();
      setDocId(document_id);
      setDocument(doc);
      setClauses(clauses);
      if (clauses.length > 0) {
        setSelected(clauses[0].id);
      }
      showSuccess('Upload complete', 'Clauses extracted and ready.');
    } catch (err: any) {
      console.error('Upload failed', err);
      showError('Upload failed', err?.message || 'Unable to process file');
    } finally {
      event.target.value = '';
      setUploading(false);
    }
  };

  return (
    <div className="h-full flex flex-col bg-white/60 backdrop-blur-sm min-h-0" style={{ fontFamily: 'Inter, ui-sans-serif, system-ui' }}>
      {/* Quick Actions */}
      <div className="px-4 py-3 border-b border-zinc-200">
        <div className="flex flex-wrap gap-2">
          {quickPrompts.map((qp) => (
            <Button
              key={qp.id}
              variant="secondary"
              size="sm"
              className="bg-zinc-100 hover:bg-zinc-200 text-zinc-800"
              onClick={() => setInput(qp.text)}
            >
              <Wand2 size={14} className="mr-1" /> {qp.label}
            </Button>
          ))}
        </div>
      </div>

      {/* Chat content */}
      <div className="flex-1 overflow-y-auto px-4 py-4 min-h-0">
        {chat.length === 0 ? (
          <div className="flex flex-col items-center justify-center text-center text-zinc-500 pt-4">
            <MessageSquareText size={32} className="mb-2 text-zinc-300" />
            <h3 className="text-sm font-medium text-zinc-700 mb-1">Welcome to Babel AI</h3>
            <p className="text-xs mb-2 max-w-md">
              I'm your VC lawyer copilot. I can help you with term sheet negotiations 
              and explain clauses.
            </p>
            <Button
              variant="outline"
              size="sm"
              className="text-sm bg-indigo-50 text-indigo-700 border-indigo-200 hover:bg-indigo-100"
              onClick={() => setInput('Start a new transaction')}
            >
              <Building2 size={14} className="mr-2" /> Start Transaction
            </Button>
          </div>
        ) : (
          <div className="space-y-3">
            {chat.map((m) => (
              <MessageBubble key={m.id} msg={m} />
            ))}
          </div>
        )}
        {loading && (
          <div className="flex items-center gap-2 text-xs text-zinc-500 mt-4">
            <Loader2 size={14} className="animate-spin" /> Generating suggestion...
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input Box */}
      <div className="border-t border-zinc-200 bg-white">
        <div className="p-6 pb-16">
          <div className="flex items-end gap-3">
            <div>
              <input
                type="file"
                ref={fileInputRef}
                className="hidden"
                accept=".pdf,.doc,.docx"
                onChange={handleFileSelected}
              />
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={triggerUpload}
                disabled={uploading}
                className="flex items-center gap-2"
              >
                {uploading ? <Loader2 size={14} className="animate-spin" /> : <UploadIcon size={16} />}
                Upload Term Sheet
              </Button>
            </div>
            <div className="relative flex-1">
            <Textarea
              placeholder="Ask to redline or explain…"
                className="w-full min-h-[44px] max-h-32 resize-none pr-12"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            <Button
              onClick={send}
              disabled={!input.trim() || loading}
              size="icon"
                className="absolute right-2 bottom-2 h-8 w-8 bg-indigo-600 hover:bg-indigo-700 disabled:bg-zinc-400"
            >
                {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
            </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

