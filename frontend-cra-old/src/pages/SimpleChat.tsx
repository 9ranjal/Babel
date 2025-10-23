/**
 * Simple Chat Interface for Negotiation Engine Testing
 * 
 * Clean white screen with chat interface for experimenting with the copilot
 */
import React, { useState, useRef, useEffect } from 'react';
import { useNegotiation } from '../hooks/useNegotiation.ts';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Send, Loader2, User, Bot, Settings } from 'lucide-react';

interface ChatMessage {
  id: string;
  role: 'user' | 'copilot';
  content: string;
  timestamp: Date;
  metadata?: {
    sessionId?: string;
    roundNo?: number;
    terms?: any;
    utilities?: any;
  };
}

export function SimpleChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [companyPersonaId, setCompanyPersonaId] = useState('');
  const [investorPersonaId, setInvestorPersonaId] = useState('');
  const [showSetup, setShowSetup] = useState(true);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const {
    createSession,
    runRound,
    currentRound,
    terms,
    loading: engineLoading,
    error
  } = useNegotiation();

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const addMessage = (role: 'user' | 'copilot', content: string, metadata?: any) => {
    const message: ChatMessage = {
      id: Date.now().toString(),
      role,
      content,
      timestamp: new Date(),
      metadata
    };
    setMessages(prev => [...prev, message]);
  };

  const handleSetup = async () => {
    if (!companyPersonaId || !investorPersonaId) {
      addMessage('copilot', 'Please provide both company and investor persona IDs to get started.');
      return;
    }

    try {
      setLoading(true);
      const session = await createSession(companyPersonaId, investorPersonaId, 'IN');
      setSessionId(session.id);
      setShowSetup(false);
      addMessage('copilot', `✅ Session created! Session ID: ${session.id.slice(0, 8)}...`);
      addMessage('copilot', 'I\'m ready to help you negotiate terms. Try asking me to "generate terms" or "run a negotiation round".');
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Unknown error';
      const errorStr = typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg);
      addMessage('copilot', `❌ Failed to create session: ${errorStr}`);
    } finally {
      setLoading(false);
    }
  };

  const handleNegotiate = async () => {
    if (!sessionId) {
      addMessage('copilot', 'Please set up a session first by providing persona IDs.');
      return;
    }

    try {
      setLoading(true);
      addMessage('copilot', '🤖 Running negotiation round...');
      
      const round = await runRound(sessionId);
      
      // Format the results
      const termsList = Object.entries(round.mediator_choice)
        .map(([key, value]) => `**${key.replace(/_/g, ' ')}**: ${JSON.stringify(value)}`)
        .join('\n');
      
      const utilities = `Company: ${round.utilities.company.toFixed(1)}/100, Investor: ${round.utilities.investor.toFixed(1)}/100`;
      
      addMessage('copilot', `🎯 **Negotiation Complete!**\n\n**Final Terms:**\n${termsList}\n\n**Utilities:** ${utilities}`, {
        sessionId,
        roundNo: round.round_no,
        terms: round.mediator_choice,
        utilities: round.utilities
      });
      
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Unknown error';
      const errorStr = typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg);
      addMessage('copilot', `❌ Negotiation failed: ${errorStr}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = input.trim();
    setInput('');
    addMessage('user', userMessage);

    // Simple command processing
    const lowerMessage = userMessage.toLowerCase();

    if (lowerMessage.includes('generate') || lowerMessage.includes('negotiate') || lowerMessage.includes('run')) {
      await handleNegotiate();
    } else if (lowerMessage.includes('setup') || lowerMessage.includes('persona')) {
      setShowSetup(true);
      addMessage('copilot', 'Please provide your persona IDs to set up a session.');
    } else if (lowerMessage.includes('help')) {
      addMessage('copilot', `**Available Commands:**
• "generate terms" or "run negotiation" - Start a negotiation round
• "setup" or "persona" - Configure persona IDs
• "help" - Show this help message

**Current Status:**
• Session: ${sessionId ? '✅ Active' : '❌ Not set up'}
• Company Persona: ${companyPersonaId ? '✅ Set' : '❌ Not set'}
• Investor Persona: ${investorPersonaId ? '✅ Set' : '❌ Not set'}`);
    } else {
      addMessage('copilot', `I understand you want to "${userMessage}". 

Try these commands:
• "generate terms" - Run a negotiation round
• "setup" - Configure persona IDs
• "help" - See all commands

I'm a negotiation copilot that can help you generate term sheets based on company and investor personas.`);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Header */}
      <div className="border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bot className="h-6 w-6 text-blue-600" />
            <h1 className="text-xl font-semibold">Negotiation Copilot</h1>
            {sessionId && (
              <Badge variant="outline" className="text-green-600">
                Session Active
              </Badge>
            )}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowSetup(!showSetup)}
          >
            <Settings className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Setup Panel */}
      {showSetup && (
        <div className="border-b border-gray-200 p-4 bg-gray-50">
          <div className="max-w-2xl mx-auto space-y-4">
            <h3 className="font-medium">Setup Session</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-700">Company Persona ID</label>
                <Input
                  placeholder="UUID of company persona"
                  value={companyPersonaId}
                  onChange={(e) => setCompanyPersonaId(e.target.value)}
                />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">Investor Persona ID</label>
                <Input
                  placeholder="UUID of investor persona"
                  value={investorPersonaId}
                  onChange={(e) => setInvestorPersonaId(e.target.value)}
                />
              </div>
            </div>
            <Button onClick={handleSetup} disabled={loading || !companyPersonaId || !investorPersonaId}>
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Create Session
            </Button>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="p-4">
          <Alert variant="destructive">
            <AlertDescription>{typeof error === 'string' ? error : JSON.stringify(error)}</AlertDescription>
          </Alert>
        </div>
      )}

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 py-8">
            <Bot className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <p>Start a conversation with the negotiation copilot</p>
            <p className="text-sm">Try: "help" or "generate terms"</p>
          </div>
        )}

        {messages.map((message) => (
          <div key={message.id} className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {message.role === 'copilot' && (
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <Bot className="h-4 w-4 text-blue-600" />
                </div>
              </div>
            )}
            
            <Card className={`max-w-3xl ${message.role === 'user' ? 'bg-blue-50' : 'bg-gray-50'}`}>
              <CardContent className="p-3">
                <div className="flex items-center gap-2 mb-2">
                  <span className="font-medium text-sm">
                    {message.role === 'user' ? 'You' : 'Copilot'}
                  </span>
                  <span className="text-xs text-gray-500">
                    {message.timestamp.toLocaleTimeString()}
                  </span>
                </div>
                <div className="whitespace-pre-wrap text-sm">
                  {message.content}
                </div>
                {message.metadata?.terms && (
                  <div className="mt-3 p-2 bg-white rounded border text-xs">
                    <strong>Terms:</strong> {JSON.stringify(message.metadata.terms, null, 2)}
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
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                <Bot className="h-4 w-4 text-blue-600" />
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

      {/* Input Area */}
      <div className="border-t border-gray-200 p-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask the copilot to generate terms, explain clauses, or help with negotiation..."
              disabled={loading}
              className="flex-1"
            />
            <Button onClick={handleSend} disabled={loading || !input.trim()}>
              <Send className="h-4 w-4" />
            </Button>
          </div>
          <div className="text-xs text-gray-500 mt-2">
            Press Enter to send • Try: "generate terms", "help", or "setup"
          </div>
        </div>
      </div>
    </div>
  );
}

export default SimpleChat;
