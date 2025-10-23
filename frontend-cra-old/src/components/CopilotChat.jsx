import React, { useEffect, useMemo, useRef, useState } from "react";
import { Button } from "../components/ui/button";
import { Textarea } from "../components/ui/textarea";
import { Badge } from "../components/ui/badge";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "../components/ui/tooltip";
import { Send, Wand2, MessageSquareText, Info, Loader2 } from "lucide-react";
import { loadInitialState, persistState } from "../mock";
import { api } from "../lib/apiClient";

const Message = ({ msg }) => {
  const isAssistant = msg.role === "assistant";
  return (
    <div className={`flex ${isAssistant ? "justify-start" : "justify-end"}`}>
      <div className={`max-w-[85%] rounded-lg px-3 py-2 text-sm leading-relaxed shadow-sm transition-colors ${
        isAssistant ? "bg-zinc-100 text-zinc-900" : "bg-indigo-600 text-white"
      }`}>
        <div className="whitespace-pre-wrap">{msg.content}</div>
        {msg.suggestion ? (
          <div className="mt-2 flex items-center gap-2 text-xs">
            <Badge className="bg-indigo-100 text-indigo-700">Suggestion</Badge>
            {msg.suggestion.clauseHint ? (
              <span className="text-zinc-700">{msg.suggestion.clauseHint}</span>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  );
};

export default function CopilotChat({ onSuggestion, currentTransaction }) {
  const [chat, setChat] = useState(loadInitialState().chat);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => {
    // Generate a proper UUID v4
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c == 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  });
  const bottomRef = useRef(null);

  useEffect(() => {
    persistState({ chat });
  }, [chat]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat, loading]);

  const send = async () => {
    if (!input.trim()) return;
    const userMsg = { id: `u-${Date.now()}`, role: "user", content: input.trim(), ts: Date.now() };
    setChat((c) => [...c, userMsg]);
    setInput("");
    setLoading(true);
    
    try {
      // Detect intent from user message and quick prompts
      const lower = userMsg.content.toLowerCase();
      let intent = 'general_chat';
      let endpoint = '/api/copilot/chat';
      
      // Check for specific intents
      if (lower.includes('explain') || lower.includes('what is') || lower.includes('tell me about')) {
        intent = 'explain_clause';
        endpoint = '/api/copilot/intent';
      } else if (lower.includes('change') || lower.includes('revise') || lower.includes('update') || lower.includes('modify')) {
        intent = 'revise_clause';
        endpoint = '/api/copilot/intent';
      } else if (lower.includes('what if') || lower.includes('simulate') || lower.includes('trade')) {
        intent = 'simulate_trade';
        endpoint = '/api/copilot/intent';
      } else if (lower.includes('regenerate') || lower.includes('new draft')) {
        intent = 'regenerate_document';
        endpoint = '/api/copilot/intent';
      }
      
      // Use appropriate endpoint based on intent
      const response = await api.post(endpoint, {
        intent,
        session_id: sessionId,
        message: userMsg.content,
        acting_as: 'founder',
        transaction_id: currentTransaction?.id || null
      });
      
      const result = response.data;
      const aiMsg = { 
        id: `a-${Date.now()}`, 
        ts: Date.now(), 
        role: "assistant",
        content: result.message,
        suggestion: result.updated_clauses && result.updated_clauses.length > 0 ? {
          id: `s-${Date.now()}`,
          type: 'update',
          clauseHint: 'AI Generated Update',
          rationale: result.message
        } : null
      };
      
      setChat((c) => [...c, aiMsg]);
      if (aiMsg.suggestion && typeof onSuggestion === "function") onSuggestion(aiMsg.suggestion);
    } catch (error) {
      console.error('Copilot API error:', error);
      const errorMsg = { 
        id: `a-${Date.now()}`, 
        ts: Date.now(), 
        role: "assistant",
        content: `Sorry, I encountered an error: ${error.message}. Please try again.`
      };
      setChat((c) => [...c, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const quickPrompts = useMemo(
    () => [
      { id: "qp1", label: "Explain Liquidation Pref", text: "Explain liquidation preference and its implications for founders" },
      { id: "qp2", label: "Review Anti-Dilution", text: "Review anti-dilution provisions and suggest founder-friendly alternatives" },
      { id: "qp3", label: "Board Composition", text: "Analyze board composition and voting rights for founder protection" },
      { id: "qp4", label: "Simulate Trade", text: "What if we trade liquidation preference for better board control?" },
      { id: "qp5", label: "Red Flags Check", text: "Review this term sheet for red flags and founder risks" },
    ],
    []
  );

  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className="h-full flex flex-col bg-white/60 backdrop-blur-sm border-r border-zinc-200" style={{ fontFamily: 'Inter, ui-sans-serif, system-ui' }}>
      <div className="px-4 py-3 flex items-center justify-between border-b border-zinc-200">
        <div className="flex items-center gap-2">
          <MessageSquareText size={18} className="text-zinc-700" />
          <div className="text-sm font-medium text-zinc-900">Copilot</div>
          <Badge className="bg-indigo-50 text-indigo-700">GPT-4</Badge>
        </div>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger className="text-zinc-500">
              <Info size={16} />
            </TooltipTrigger>
            <TooltipContent className="max-w-xs text-xs">
              AI responses are mocked in this preview. Backend and real LLM will be integrated next.
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      <div className="px-4 py-3">
        <div className="flex flex-wrap gap-2">
          {quickPrompts.map((qp) => (
            <Button
              key={qp.id}
              variant="secondary"
              className="h-8 px-2 py-0 text-xs bg-zinc-100 hover:bg-zinc-200 text-zinc-800"
              onClick={() => setInput(qp.text)}
            >
              <Wand2 size={14} className="mr-1" /> {qp.label}
            </Button>
          ))}
        </div>
      </div>

      <div className="flex-1 px-4 overflow-auto space-y-3">
        {chat.map((m) => (
          <Message key={m.id} msg={m} />
        ))}
        {loading ? (
          <div className="flex items-center gap-2 text-xs text-zinc-500">
            <Loader2 size={14} className="animate-spin" /> Generating suggestion...
          </div>
        ) : null}
        <div ref={bottomRef} />
      </div>

      <div className="p-3 border-t border-zinc-200">
        <div className="bg-white rounded-lg border border-zinc-300 p-2 focus-within:ring-2 focus-within:ring-indigo-200">
          <Textarea
            placeholder="Ask to redline or explain… (Enter to send, Shift+Enter for newline)"
            className="min-h-[60px] resize-none focus-visible:ring-0 focus:outline-none"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
          />
          <div className="flex justify-end mt-2">
            <Button onClick={send} disabled={!input.trim() || loading} className="bg-indigo-600 hover:bg-indigo-700">
              {loading ? <Loader2 size={16} className="animate-spin mr-2" /> : <Send size={16} className="mr-2" />} Send
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
