/**
 * Main TermCraft Application
 * 
 * Transaction-first architecture with conversational persona intake,
 * Draft 0 generation, and negotiation rounds
 */
import React, { useState, useEffect } from 'react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Separator } from '../components/ui/separator';
import { 
  Sparkles, 
  Users, 
  FileText, 
  MessageSquare, 
  Settings,
  Plus,
  ArrowRight,
  CheckCircle
} from 'lucide-react';
import TransactionSelector from '../components/TransactionSelector.tsx';
import PersonaIntake from '../components/PersonaIntake.tsx';
import RealTimeCopilotChat from '../components/RealTimeCopilotChat.tsx';
import TermSheetEditor from '../components/TermSheetEditor';
import { api } from '../lib/apiClient';

interface Transaction {
  id: string;
  name: string | null;
  created_at: string;
  owner_user: string;
}

interface TransactionPersona {
  id: string;
  transaction_id: string;
  kind: 'company' | 'investor';
  label: string | null;
  persona_id: string;
  created_at: string;
}

interface Draft0Clause {
  id: string;
  title: string;
  content_md: string;
  redlines: string[];
  citations: any[];
  current_value: Record<string, any>;
  default_band?: [number, number];
  walk_away?: [number, number];
}

interface Draft0Response {
  session_id: string;
  company_persona_id: string;
  investor_persona_ids: string[];
  clauses: Draft0Clause[];
  summary_md: string;
  utilities: Record<string, number>;
  anchor_investor?: string;
  created_at: string;
}

type AppStep = 'transaction' | 'personas' | 'draft0' | 'negotiation';

export function TermCraftApp() {
  const [currentStep, setCurrentStep] = useState<AppStep>('transaction');
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);
  const [transactionPersonas, setTransactionPersonas] = useState<TransactionPersona[]>([]);
  const [draft0, setDraft0] = useState<Draft0Response | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load transaction personas when transaction is selected
  useEffect(() => {
    if (selectedTransaction) {
      loadTransactionPersonas(selectedTransaction.id);
    }
  }, [selectedTransaction]);

  const loadTransactionPersonas = async (transactionId: string) => {
    try {
      const response = await api.get(`/api/transactions/${transactionId}/personas`);
      setTransactionPersonas(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load personas');
    }
  };

  const handleTransactionSelect = (transactionId: string) => {
    // Find the transaction from the list (in a real app, you'd fetch it)
    const transaction: Transaction = {
      id: transactionId,
      name: 'Selected Transaction',
      created_at: new Date().toISOString(),
      owner_user: 'current-user'
    };
    setSelectedTransaction(transaction);
    setCurrentStep('personas');
  };

  const handlePersonaCreated = (personaId: string, role: 'founder' | 'investor') => {
    // Reload personas to show the new one
    if (selectedTransaction) {
      loadTransactionPersonas(selectedTransaction.id);
    }
  };

  const handlePersonaIntakeComplete = () => {
    // Check if we have both company and investor personas
    const hasCompany = transactionPersonas.some(p => p.kind === 'company');
    const hasInvestor = transactionPersonas.some(p => p.kind === 'investor');
    
    if (hasCompany && hasInvestor) {
      setCurrentStep('draft0');
    } else {
      // Stay on personas step to create more
      setCurrentStep('personas');
    }
  };

  const generateDraft0 = async () => {
    if (!selectedTransaction) return;
    
    const companyPersona = transactionPersonas.find(p => p.kind === 'company');
    const investorPersonas = transactionPersonas.filter(p => p.kind === 'investor');
    
    if (!companyPersona || investorPersonas.length === 0) {
      setError('Need both company and investor personas to generate Draft 0');
      return;
    }

    try {
      setLoading(true);
      const response = await api.post('/api/copilot/draft0', {
        company_persona_id: companyPersona.persona_id,
        investor_persona_ids: investorPersonas.map(p => p.persona_id),
        stage: 'seed',
        region: 'SG',
        clauses_enabled: ['exclusivity', 'pro_rata_rights', 'vesting'],
        transaction_id: selectedTransaction.id
      });
      
      setDraft0(response.data);
      setCurrentStep('negotiation');
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to generate Draft 0');
    } finally {
      setLoading(false);
    }
  };

  const getStepStatus = (step: AppStep) => {
    switch (step) {
      case 'transaction':
        return selectedTransaction ? 'complete' : 'current';
      case 'personas':
        const hasCompany = transactionPersonas.some(p => p.kind === 'company');
        const hasInvestor = transactionPersonas.some(p => p.kind === 'investor');
        if (hasCompany && hasInvestor) return 'complete';
        if (hasCompany || hasInvestor) return 'current';
        return 'pending';
      case 'draft0':
        return draft0 ? 'complete' : 'current';
      case 'negotiation':
        return draft0 ? 'current' : 'pending';
      default:
        return 'pending';
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 'transaction':
        return (
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-8">
              <Sparkles className="h-12 w-12 mx-auto mb-4 text-indigo-600" />
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Welcome to TermCraft AI</h1>
              <p className="text-lg text-gray-600">
                Create and negotiate term sheets with AI-powered insights
              </p>
            </div>
            <TransactionSelector onTransactionSelect={handleTransactionSelect} />
          </div>
        );

      case 'personas':
        return (
          <div className="max-w-4xl mx-auto space-y-6">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Create Personas</h2>
              <p className="text-gray-600">
                Set up company and investor personas for your negotiation
              </p>
            </div>

            <div className="grid gap-6">
              {/* Existing Personas */}
              {transactionPersonas.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Users className="h-5 w-5" />
                      Current Personas
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid gap-3">
                      {transactionPersonas.map((persona) => (
                        <div key={persona.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <div className="flex items-center gap-3">
                            <Badge variant={persona.kind === 'company' ? 'default' : 'secondary'}>
                              {persona.kind === 'company' ? 'Company' : 'Investor'}
                            </Badge>
                            <span className="font-medium">{persona.label || `${persona.kind} persona`}</span>
                          </div>
                          <CheckCircle className="h-5 w-5 text-green-600" />
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Create New Persona */}
              <PersonaIntake
                transactionId={selectedTransaction!.id}
                onPersonaCreated={handlePersonaCreated}
                onComplete={handlePersonaIntakeComplete}
              />
            </div>
          </div>
        );

      case 'draft0':
        return (
          <div className="max-w-4xl mx-auto space-y-6">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Generate Draft 0</h2>
              <p className="text-gray-600">
                Create your initial term sheet based on the personas
              </p>
            </div>

            <Card>
              <CardContent className="p-6">
                <div className="text-center">
                  <FileText className="h-12 w-12 mx-auto mb-4 text-indigo-600" />
                  <h3 className="text-lg font-semibold mb-2">Ready to Generate Draft 0</h3>
                  <p className="text-gray-600 mb-6">
                    Based on your personas, I'll create an initial term sheet with:
                  </p>
                  <ul className="text-left max-w-md mx-auto space-y-2 text-sm text-gray-600">
                    <li>• Exclusivity clauses</li>
                    <li>• Pro-rata rights</li>
                    <li>• Vesting schedules</li>
                    <li>• Market-appropriate terms</li>
                  </ul>
                  <Button 
                    onClick={generateDraft0}
                    disabled={loading}
                    className="mt-6 bg-indigo-600 hover:bg-indigo-700"
                  >
                    {loading ? 'Generating...' : 'Generate Draft 0'}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        );

      case 'negotiation':
        return (
          <div className="h-screen flex flex-col">
            <div className="border-b border-gray-200 p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-6 w-6 text-indigo-600" />
                  <h1 className="text-xl font-semibold">TermCraft AI</h1>
                  <Badge className="bg-green-100 text-green-700">Draft 0 Generated</Badge>
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm">
                    <Settings className="h-4 w-4 mr-2" />
                    Settings
                  </Button>
                </div>
              </div>
            </div>

            <div className="flex-1 grid grid-cols-2">
              <div className="border-r border-gray-200">
                <RealTimeCopilotChat 
                  sessionId={draft0?.session_id}
                  transactionId={selectedTransaction?.id}
                />
              </div>
              <div>
                <TermSheetEditor />
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Progress Steps */}
      {currentStep !== 'negotiation' && (
        <div className="bg-white border-b border-gray-200">
          <div className="max-w-4xl mx-auto px-4 py-6">
            <div className="flex items-center justify-between">
              {[
                { key: 'transaction', label: 'Transaction', icon: Sparkles },
                { key: 'personas', label: 'Personas', icon: Users },
                { key: 'draft0', label: 'Draft 0', icon: FileText },
                { key: 'negotiation', label: 'Negotiate', icon: MessageSquare }
              ].map((step, index) => {
                const status = getStepStatus(step.key as AppStep);
                const Icon = step.icon;
                
                return (
                  <div key={step.key} className="flex items-center">
                    <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${
                      status === 'complete' ? 'bg-green-100 text-green-700' :
                      status === 'current' ? 'bg-indigo-100 text-indigo-700' :
                      'bg-gray-100 text-gray-500'
                    }`}>
                      <Icon className="h-4 w-4" />
                      <span className="text-sm font-medium">{step.label}</span>
                    </div>
                    {index < 3 && (
                      <ArrowRight className="h-4 w-4 mx-2 text-gray-400" />
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border-b border-red-200 p-4">
          <div className="max-w-4xl mx-auto">
            <p className="text-red-600">{error}</p>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1">
        {renderStepContent()}
      </div>
    </div>
  );
}

export default TermCraftApp;
