/**
 * Real-Time Copilot Chat Component
 * 
 * Integrates with backend copilot intents API for real AI responses
 * Supports explain_clause, revise_clause, simulate_trade, etc.
 */
import React, { useState, useRef, useEffect } from 'react';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { Badge } from './ui/badge';
import { Card, CardContent } from './ui/card';
import { ScrollArea } from './ui/scroll-area';
import { Send, Bot, User, Loader2, MessageSquare, Sparkles } from 'lucide-react';
import { api } from '../lib/apiClient';

interface ChatMessage {
  id: string;
  role: 'user' | 'copilot';
  content: string;
  timestamp: Date;
  intent?: string;
  success?: boolean;
  citations?: any[];
  utilities?: Record<string, number>;
  suggested_trades?: string[];
}

interface RealTimeCopilotChatProps {
  sessionId?: string;
  transactionId?: string;
  onSuggestion?: (suggestion: any) => void;
}

export function RealTimeCopilotChat({ 
  sessionId, 
  transactionId, 
  onSuggestion 
}: RealTimeCopilotChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Add welcome message
    if (messages.length === 0) {
      addMessage('copilot', `Welcome to TermCraft AI! I can help you:

• **Explain clauses** - "What does liquidation preference mean?"
• **Revise terms** - "Change valuation cap to $15M"  
• **Simulate trades** - "What if we increase the discount to 25%?"
• **Update personas** - "The investor is more risk-averse"

What would you like to do?`);
    }
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const addMessage = (role: 'user' | 'copilot', content: string, metadata?: any) => {
    const message: ChatMessage = {
      id: Date.now().toString(),
      role,
      content,
      timestamp: new Date(),
      ...metadata
    };
    setMessages(prev => [...prev, message]);
  };

  const detectIntent = (message: string): string => {
    const lower = message.toLowerCase();
    
    if (lower.includes('explain') || lower.includes('what does') || lower.includes('mean')) {
      return 'explain_clause';
    }
    if (lower.includes('change') || lower.includes('revise') || lower.includes('update') || lower.includes('modify')) {
      return 'revise_clause';
    }
    if (lower.includes('what if') || lower.includes('simulate') || lower.includes('scenario')) {
      return 'simulate_trade';
    }
    if (lower.includes('regenerate') || lower.includes('new draft') || lower.includes('refresh')) {
      return 'regenerate_document';
    }
    if (lower.includes('persona') || lower.includes('update') || lower.includes('change')) {
      return 'update_persona';
    }
    
    return 'explain_clause'; // Default intent
  };

  const extractClauseKey = (message: string): string | null => {
    const lower = message.toLowerCase();
    
    if (lower.includes('valuation') || lower.includes('cap')) return 'valuation_cap';
    if (lower.includes('discount')) return 'discount';
    if (lower.includes('liquidation') || lower.includes('preference')) return 'liquidation_preference';
    if (lower.includes('pro rata') || lower.includes('prorata')) return 'pro_rata_rights';
    if (lower.includes('vesting')) return 'vesting';
    if (lower.includes('exclusivity')) return 'exclusivity';
    
    return null;
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    addMessage('user', userMessage);

    try {
      setLoading(true);
      setError(null);

      const intent = detectIntent(userMessage);
      const clauseKey = extractClauseKey(userMessage);

      const response = await api.post('/api/copilot/intent', {
        intent,
        session_id: sessionId,
        clause_key: clauseKey,
        message: userMessage,
        transaction_id: transactionId,
        acting_as: 'founder' // Default, could be dynamic
      });

      const result = response.data;
      
      // Handle the response based on intent
      let responseContent = result.message;
      
      if (result.success) {
        if (result.updated_clauses && result.updated_clauses.length > 0) {
          responseContent += '\n\n**Updated Clauses:**';
          result.updated_clauses.forEach((clause: any) => {
            responseContent += `\n• ${clause.title}: ${JSON.stringify(clause.current_value)}`;
          });
        }
        
        if (result.utilities && Object.keys(result.utilities).length > 0) {
          responseContent += '\n\n**Utilities:**';
          Object.entries(result.utilities).forEach(([key, value]) => {
            responseContent += `\n• ${key}: ${value.toFixed(1)}/100`;
          });
        }
        
        if (result.suggested_trades && result.suggested_trades.length > 0) {
          responseContent += '\n\n**Suggested Trades:**';
          result.suggested_trades.forEach((trade: string) => {
            responseContent += `\n• ${trade}`;
          });
        }
      }

      addMessage('copilot', responseContent, {
        intent: result.intent,
        success: result.success,
        citations: result.citations,
        utilities: result.utilities,
        suggested_trades: result.suggested_trades
      });

      // Trigger suggestion callback if there are updated clauses
      if (result.updated_clauses && onSuggestion) {
        result.updated_clauses.forEach((clause: any) => {
          onSuggestion({
            id: `suggestion-${Date.now()}`,
            type: 'update',
            clause_key: clause.id,
            title: clause.title,
            content: clause.content_md,
            rationale: 'AI-generated update',
            clauseHint: clause.title
          });
        });
      }

    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to process request';
      addMessage('copilot', `❌ Error: ${errorMsg}`);
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const quickPrompts = [
    { label: 'Explain Valuation Cap', text: 'Explain the valuation cap clause' },
    { label: 'Change Discount', text: 'Change the discount to 15%' },
    { label: 'Simulate Trade', text: 'What if we increase the liquidation preference to 2x?' },
    { label: 'Regenerate Draft', text: 'Regenerate the term sheet with updated terms' }
  ];

  return (
    <div className="h-full flex flex-col bg-white border-r border-gray-200">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-indigo-600" />
          <h2 className="font-semibold text-gray-900">AI Copilot</h2>
          <Badge className="bg-green-100 text-green-700">Live</Badge>
        </div>
        <p className="text-sm text-gray-600 mt-1">
          Powered by Ollama • Connected to backend
        </p>
      </div>

      {/* Quick Prompts */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex flex-wrap gap-2">
          {quickPrompts.map((prompt, index) => (
            <Button
              key={index}
              variant="outline"
              size="sm"
              className="text-xs"
              onClick={() => setInput(prompt.text)}
            >
              {prompt.label}
            </Button>
          ))}
        </div>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {messages.map((message) => (
            <div key={message.id} className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {message.role === 'copilot' && (
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center">
                    <Bot className="h-4 w-4 text-indigo-600" />
                  </div>
                </div>
              )}
              
              <Card className={`max-w-[85%] ${message.role === 'user' ? 'bg-indigo-50' : 'bg-gray-50'}`}>
                <CardContent className="p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-medium text-sm">
                      {message.role === 'user' ? 'You' : 'Copilot'}
                    </span>
                    <span className="text-xs text-gray-500">
                      {message.timestamp.toLocaleTimeString()}
                    </span>
                    {message.intent && (
                      <Badge variant="outline" className="text-xs">
                        {message.intent.replace('_', ' ')}
                      </Badge>
                    )}
                  </div>
                  <div className="whitespace-pre-wrap text-sm">
                    {message.content}
                  </div>
                  {message.citations && message.citations.length > 0 && (
                    <div className="mt-2 text-xs text-gray-600">
                      <strong>Citations:</strong> {message.citations.length} sources
                    </div>
                  )}
                </CardContent>
              </Card>

              {message.role === 'user' && (
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
                    <User className="h-4 w-4 text-gray-600" />
                  </div>
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex gap-3 justify-start">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center">
                  <Bot className="h-4 w-4 text-indigo-600" />
                </div>
              </div>
              <Card className="bg-gray-50">
                <CardContent className="p-3">
                  <div className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span className="text-sm">Copilot is thinking...</span>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Error Display */}
      {error && (
        <div className="p-3 bg-red-50 border-t border-red-200">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex gap-2">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask the copilot to explain, revise, or simulate terms..."
            className="flex-1 min-h-[60px] resize-none"
            disabled={loading}
          />
          <Button 
            onClick={handleSend}
            disabled={!input.trim() || loading}
            className="bg-indigo-600 hover:bg-indigo-700"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
        <div className="text-xs text-gray-500 mt-2">
          Press Enter to send • Try: "explain liquidation preference" or "change valuation cap to $12M"
        </div>
      </div>
    </div>
  );
}

export default RealTimeCopilotChat;
