import React, { useCallback, useState, useEffect } from "react";
import CopilotChat from "../components/CopilotChat";
import TermSheetEditor from "../components/TermSheetEditor";
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from "../components/ui/resizable";
import { Button } from "../components/ui/button";
import { Avatar, AvatarFallback } from "../components/ui/avatar";
import { CreditCard, HelpCircle, Sparkles, Plus, ChevronDown } from "lucide-react";
import { api } from "../lib/apiClient";

export default function TermSheetCopilot() {
  const [incomingSuggestion, setIncomingSuggestion] = useState(null);
  const [currentTransaction, setCurrentTransaction] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [showTransactionSelector, setShowTransactionSelector] = useState(false);

  const onSuggestion = useCallback((s) => {
    setIncomingSuggestion(s);
    setTimeout(() => setIncomingSuggestion(null), 0);
  }, []);

  // Load transactions on mount
  useEffect(() => {
    const loadTransactions = async () => {
      try {
        const response = await api.get('/api/copilot/transactions');
        setTransactions(response.data);
        if (response.data.length > 0) {
          setCurrentTransaction(response.data[0]);
        }
      } catch (error) {
        console.error('Failed to load transactions:', error);
      }
    };
    loadTransactions();
  }, []);

  const createNewTransaction = async () => {
    try {
      const response = await api.post('/api/transactions', {
        name: `Term Sheet ${new Date().toLocaleDateString()}`
      });
      const newTx = response.data;
      setTransactions(prev => [newTx, ...prev]);
      setCurrentTransaction(newTx);
      setShowTransactionSelector(false);
    } catch (error) {
      console.error('Failed to create transaction:', error);
    }
  };

  return (
    <div className="h-screen w-screen bg-zinc-100 text-zinc-900" style={{ fontFamily: 'Inter, ui-sans-serif, system-ui' }}>
      {/* App Header */}
      <div className="h-12 border-b border-zinc-200 bg-white flex items-center justify-between px-4">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Sparkles size={16} className="text-indigo-600" />
            <div className="text-sm font-medium tracking-wide">Termcraft AI</div>
          </div>
          
          {/* Transaction Selector */}
          <div className="relative">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => setShowTransactionSelector(!showTransactionSelector)}
              className="flex items-center gap-2"
            >
              {currentTransaction ? currentTransaction.name : 'Select Transaction'}
              <ChevronDown size={14} />
            </Button>
            
            {showTransactionSelector && (
              <div className="absolute top-full left-0 mt-1 w-64 bg-white border border-zinc-200 rounded-lg shadow-lg z-50">
                <div className="p-2">
                  <Button 
                    size="sm" 
                    onClick={createNewTransaction}
                    className="w-full justify-start gap-2 mb-2"
                  >
                    <Plus size={14} />
                    New Transaction
                  </Button>
                  <div className="max-h-48 overflow-y-auto">
                    {transactions.map(tx => (
                      <button
                        key={tx.id}
                        onClick={() => {
                          setCurrentTransaction(tx);
                          setShowTransactionSelector(false);
                        }}
                        className={`w-full text-left px-3 py-2 text-sm rounded hover:bg-zinc-100 ${
                          currentTransaction?.id === tx.id ? 'bg-indigo-50 text-indigo-700' : ''
                        }`}
                      >
                        {tx.name}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" className="bg-zinc-100 hover:bg-zinc-200 text-zinc-800 h-8 px-3">
            <HelpCircle size={14} className="mr-1" /> Help
          </Button>
          <Avatar className="h-8 w-8">
            <AvatarFallback className="bg-indigo-50 text-indigo-700 text-xs">TC</AvatarFallback>
          </Avatar>
        </div>
      </div>

      {/* Main Panels */}
      <ResizablePanelGroup direction="horizontal" className="h-[calc(100vh-48px)]">
        <ResizablePanel defaultSize={40} minSize={28} maxSize={55}>
          <CopilotChat onSuggestion={onSuggestion} currentTransaction={currentTransaction} />
        </ResizablePanel>
        <ResizableHandle withHandle />
        <ResizablePanel defaultSize={60} minSize={45}>
          <TermSheetEditor incomingSuggestion={incomingSuggestion} />
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
}
