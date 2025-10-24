import React, { useEffect, useMemo, useRef, useState } from "react";
import { Button } from "../components/ui/button";
import { Textarea } from "../components/ui/textarea";
import { Badge } from "../components/ui/badge";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "../components/ui/tooltip";
import { Send, Wand2, MessageSquareText, Info, Loader2, Building2, Users, DollarSign, FileText, Trash2, Plus } from "lucide-react";
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

  const infoCollectionPills = useMemo(
    () => [
      { 
        id: "company_info", 
        label: "Company Info", 
        icon: Building2,
        text: "I need to collect company information for the term sheet. What's your company name, industry, funding stage, and annual revenue?",
        color: "bg-blue-50 text-blue-700 border-blue-200"
      },
      { 
        id: "investor_info", 
        label: "Investor Details", 
        icon: Users,
        text: "Tell me about your investors - who's the lead investor, what type of investor are they, and what's the investment amount and pre-money valuation?",
        color: "bg-green-50 text-green-700 border-green-200"
      },
      { 
        id: "deal_terms", 
        label: "Deal Structure", 
        icon: DollarSign,
        text: "What are the key deal terms - equity percentage, liquidation preference, board composition, and anti-dilution protection?",
        color: "bg-purple-50 text-purple-700 border-purple-200"
      },
      { 
        id: "additional_terms", 
        label: "Other Terms", 
        icon: FileText,
        text: "Any other important terms - exclusivity period, founder vesting schedule, drag-along and tag-along rights?",
        color: "bg-orange-50 text-orange-700 border-orange-200"
      },
    ],
    []
  );

  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const clearChat = () => {
    setChat([]);
    setInput("");
    // Clear persisted state
    persistState({ chat: [] });
  };

  const startNewChat = () => {
    clearChat();
    // Optionally add a welcome message
    const welcomeMsg = {
      id: `a-${Date.now()}`,
      role: "assistant",
      content: "Hello! I'm your VC lawyer copilot. I can help you with term sheet negotiations, explain clauses, and collect information for generating term sheets. How can I assist you today?",
      ts: Date.now()
    };
    setChat([welcomeMsg]);
  };

  return (
    <div className="h-full flex flex-col bg-white/60 backdrop-blur-sm border-r border-zinc-200 min-h-0" style={{ fontFamily: 'Inter, ui-sans-serif, system-ui' }}>
      <div className="px-4 py-3 flex items-center justify-between border-b border-zinc-200 h-12">
        <div className="flex items-center gap-2">
          <MessageSquareText size={18} className="text-zinc-700" />
          <div className="text-sm font-medium text-zinc-900">Copilot</div>
        </div>
        <div className="flex items-center gap-2">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button 
                  variant="ghost" 
                  size="icon" 
                  className="h-8 w-8 text-zinc-500 hover:text-zinc-700"
                  onClick={startNewChat}
                >
                  <Plus size={16} />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Start New Chat</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button 
                  variant="ghost" 
                  size="icon" 
                  className="h-8 w-8 text-zinc-500 hover:text-zinc-700"
                  onClick={clearChat}
                >
                  <Trash2 size={16} />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Clear Chat History</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

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
      </div>

      {/* Quick Actions - right below copilot bar */}
      <div className="px-4 py-3 border-b border-zinc-200">
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

      {/* Chat content - scrollable with height constraint */}
      <div className="flex-1 overflow-y-auto px-4 py-4 min-h-0">
        {chat.length === 0 ? (
          <div className="flex flex-col items-center justify-center text-center text-zinc-500 pt-4">
            <MessageSquareText size={32} className="mb-2 text-zinc-300" />
            <h3 className="text-sm font-medium text-zinc-700 mb-1">Welcome to Termcraft AI</h3>
            <p className="text-xs mb-2 max-w-md">
              I'm your VC lawyer copilot. I can help you with term sheet negotiations, 
              explain clauses, and collect information for generating term sheets.
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              {infoCollectionPills.slice(0, 2).map((pill) => (
                <Button
                  key={pill.id}
                  variant="outline"
                  size="sm"
                  className={`text-xs ${pill.color}`}
                  onClick={() => setInput(pill.text)}
                >
                  <pill.icon size={12} className="mr-1" /> {pill.label}
                </Button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {chat.map((m) => (
              <Message key={m.id} msg={m} />
            ))}
            {loading ? (
              <div className="flex items-center gap-2 text-xs text-zinc-500">
                <Loader2 size={14} className="animate-spin" /> Generating suggestion...
              </div>
            ) : null}
          </>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input Box - separate component with padding */}
      <div className="border-t border-zinc-200 bg-white">
        <div className="p-6 pb-16">
          <div className="relative">
            <Textarea
              placeholder="Ask to redline or explain…"
              className="w-full min-h-[44px] max-h-32 resize-none pr-10 border-zinc-300 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-lg"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
            />
            <Button
              onClick={send}
              disabled={!input.trim() || loading}
              size="icon"
              className="absolute right-2 bottom-2 h-7 w-7 bg-indigo-600 hover:bg-indigo-700 disabled:bg-zinc-400"
            >
              {loading ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}