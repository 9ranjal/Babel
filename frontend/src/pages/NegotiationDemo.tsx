/**
 * NegotiationDemo Page
 * 
 * Demo page showing how to use the negotiation engine
 */
import React, { useState, useEffect } from 'react';
import { useNegotiation } from '../hooks/useNegotiation';
import { NegotiationPanel } from '../components/NegotiationPanel';
import { TermsDisplay } from '../components/TermsDisplay';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Loader2, Play, RefreshCw } from 'lucide-react';

export function NegotiationDemo() {
  const {
    session,
    currentRound,
    terms,
    rounds,
    loading,
    error,
    createSession,
    runRound,
    getSession,
    getSessionTerms,
    getSessionRounds,
    updateTerm,
    clearError
  } = useNegotiation();

  const [companyPersonaId, setCompanyPersonaId] = useState('');
  const [investorPersonaId, setInvestorPersonaId] = useState('');
  const [sessionId, setSessionId] = useState('');

  // Auto-load session if ID is in URL or localStorage
  useEffect(() => {
    const savedSessionId = localStorage.getItem('demo_session_id');
    if (savedSessionId && !session) {
      setSessionId(savedSessionId);
      loadSession(savedSessionId);
    }
  }, []);

  const loadSession = async (id: string) => {
    try {
      await getSession(id);
      await getSessionTerms(id);
      await getSessionRounds(id);
      localStorage.setItem('demo_session_id', id);
    } catch (err) {
      console.error('Failed to load session:', err);
    }
  };

  const handleCreateSession = async () => {
    if (!companyPersonaId || !investorPersonaId) {
      alert('Please enter both persona IDs');
      return;
    }

    try {
      const newSession = await createSession(companyPersonaId, investorPersonaId, 'IN');
      setSessionId(newSession.id);
      localStorage.setItem('demo_session_id', newSession.id);
    } catch (err) {
      console.error('Failed to create session:', err);
    }
  };

  const handleRunRound = async () => {
    if (!session) {
      alert('Please create or load a session first');
      return;
    }

    try {
      await runRound(session.id);
    } catch (err) {
      console.error('Failed to run round:', err);
    }
  };

  const handleTogglePin = async (clauseKey: string, currentlyPinned: boolean) => {
    if (!session) return;

    try {
      const term = terms.find(t => t.clause_key === clauseKey);
      if (!term) return;

      await updateTerm(
        session.id,
        clauseKey,
        term.value,
        currentlyPinned ? undefined : 'system'
      );
    } catch (err) {
      console.error('Failed to toggle pin:', err);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Negotiation Engine Demo</h1>
        {session && (
          <div className="text-sm text-gray-500">
            Session: {session.id.slice(0, 8)}... • Status: {session.status}
          </div>
        )}
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>
            {error}
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={clearError}
              className="ml-2"
            >
              Dismiss
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Session Setup */}
      {!session && (
        <Card>
          <CardHeader>
            <CardTitle>Create Negotiation Session</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="company-persona">Company Persona ID</Label>
                <Input
                  id="company-persona"
                  placeholder="UUID of company persona"
                  value={companyPersonaId}
                  onChange={(e) => setCompanyPersonaId(e.target.value)}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="investor-persona">Investor Persona ID</Label>
                <Input
                  id="investor-persona"
                  placeholder="UUID of investor persona"
                  value={investorPersonaId}
                  onChange={(e) => setInvestorPersonaId(e.target.value)}
                />
              </div>
            </div>

            <div className="flex gap-2">
              <Button 
                onClick={handleCreateSession}
                disabled={loading || !companyPersonaId || !investorPersonaId}
              >
                {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Create Session
              </Button>
              
              <div className="flex items-center gap-2 ml-4">
                <span className="text-sm text-gray-500">Or load existing:</span>
                <Input
                  placeholder="Session ID"
                  className="w-64"
                  value={sessionId}
                  onChange={(e) => setSessionId(e.target.value)}
                />
                <Button 
                  variant="outline"
                  onClick={() => loadSession(sessionId)}
                  disabled={!sessionId || loading}
                >
                  Load
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Controls */}
      {session && (
        <Card>
          <CardHeader>
            <CardTitle>Negotiation Controls</CardTitle>
          </CardHeader>
          <CardContent className="flex gap-2">
            <Button 
              onClick={handleRunRound}
              disabled={loading}
              size="lg"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Running Round...
                </>
              ) : (
                <>
                  <Play className="mr-2 h-5 w-5" />
                  Run Negotiation Round
                </>
              )}
            </Button>
            
            <Button 
              variant="outline"
              onClick={() => loadSession(session.id)}
              disabled={loading}
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Results Layout */}
      {session && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left: Current Terms */}
          <div>
            <TermsDisplay 
              terms={terms}
              onTogglePin={handleTogglePin}
            />
          </div>

          {/* Right: Negotiation Results */}
          <div>
            <NegotiationPanel 
              round={currentRound}
              loading={loading}
            />
          </div>
        </div>
      )}

      {/* Round History */}
      {session && rounds.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Round History ({rounds.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {rounds.map((round) => (
                <div key={round.round_no} className="flex items-center justify-between p-2 border rounded">
                  <span className="font-medium">Round {round.round_no}</span>
                  <div className="flex gap-4 text-sm">
                    <span>Company: {round.utilities?.company?.toFixed(1) || 'N/A'}</span>
                    <span>Investor: {round.utilities?.investor?.toFixed(1) || 'N/A'}</span>
                  </div>
                  <Button 
                    size="sm" 
                    variant="ghost"
                    onClick={() => {
                      // Could implement round selection to view historical data
                      console.log('View round:', round);
                    }}
                  >
                    View
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Instructions */}
      {!session && (
        <Card className="bg-blue-50 border-blue-200">
          <CardHeader>
            <CardTitle>Getting Started</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p><strong>1.</strong> Create personas in Supabase (company & investor) with stage/region attrs</p>
            <p><strong>2.</strong> Copy the persona UUIDs and paste them above</p>
            <p><strong>3.</strong> Click "Create Session" to start a new negotiation</p>
            <p><strong>4.</strong> Click "Run Negotiation Round" to generate terms</p>
            <p><strong>5.</strong> View results: terms, traces, citations, and utilities</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default NegotiationDemo;

