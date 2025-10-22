/**
 * useNegotiation hook
 * 
 * Manages negotiation state and API calls
 */
import { useState, useCallback } from 'react';
import { api } from '../lib/apiClient';

export interface TermValue {
  [key: string]: any;
}

export interface TermProposal {
  clause_key: string;
  value: TermValue;
  rationale: string;
  snippet_ids: number[];
}

export interface NegotiationTrace {
  clause_key: string;
  company_proposal: TermValue;
  investor_proposal: TermValue;
  final_value: TermValue;
  rationale: string;
  snippet_ids: number[];
  confidence: number;
}

export interface EmbeddedSnippet {
  id: number;
  clause_key: string;
  perspective: 'detail' | 'founder' | 'investor' | 'batna' | 'balance';
  stage?: string;
  region?: string;
  content: string;
  tags?: Record<string, any>;
}

export interface NegotiationRound {
  session_id: string;
  round_no: number;
  company_proposal: Record<string, TermValue>;
  investor_proposal: Record<string, TermValue>;
  mediator_choice: Record<string, TermValue>;
  utilities: {
    company: number;
    investor: number;
  };
  rationale_md: string;
  traces: NegotiationTrace[];
  citations: EmbeddedSnippet[];
  grades?: {
    policy_ok: boolean;
    grounding: number;
    validation_errors?: string[];
  };
  decided: boolean;
  created_at?: string;
}

export interface NegotiationSession {
  id: string;
  owner_user: string;
  company_persona: string;
  investor_persona: string;
  regime: string;
  status: 'draft' | 'negotiating' | 'final';
  created_at: string;
  updated_at: string;
}

export interface SessionTerm {
  session_id: string;
  clause_key: string;
  value: TermValue;
  source: 'rule' | 'persona' | 'copilot';
  confidence?: number;
  pinned_by?: 'company' | 'investor' | 'system';
  created_at: string;
  updated_at: string;
}

export interface UseNegotiationReturn {
  session: NegotiationSession | null;
  currentRound: NegotiationRound | null;
  terms: SessionTerm[];
  rounds: any[];
  loading: boolean;
  error: string | null;
  
  createSession: (companyPersonaId: string, investorPersonaId: string, regime?: string) => Promise<NegotiationSession>;
  runRound: (sessionId: string, roundNo?: number, userOverrides?: Record<string, TermValue>) => Promise<NegotiationRound>;
  getSession: (sessionId: string) => Promise<NegotiationSession>;
  getSessionTerms: (sessionId: string) => Promise<SessionTerm[]>;
  getSessionRounds: (sessionId: string) => Promise<any[]>;
  updateTerm: (sessionId: string, clauseKey: string, value: TermValue, pinnedBy?: string) => Promise<SessionTerm>;
  clearError: () => void;
}

export function useNegotiation(): UseNegotiationReturn {
  const [session, setSession] = useState<NegotiationSession | null>(null);
  const [currentRound, setCurrentRound] = useState<NegotiationRound | null>(null);
  const [terms, setTerms] = useState<SessionTerm[]>([]);
  const [rounds, setRounds] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const createSession = useCallback(async (
    companyPersonaId: string,
    investorPersonaId: string,
    regime: string = 'IN'
  ): Promise<NegotiationSession> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.post('/api/negotiate/session', {
        company_persona: companyPersonaId,
        investor_persona: investorPersonaId,
        regime,
        status: 'draft'
      });
      
      const newSession = response.data as NegotiationSession;
      setSession(newSession);
      return newSession;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to create session';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, []);

  const runRound = useCallback(async (
    sessionId: string,
    roundNo?: number,
    userOverrides?: Record<string, TermValue>
  ): Promise<NegotiationRound> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.post('/api/negotiate/round', {
        session_id: sessionId,
        round_no: roundNo,
        user_overrides: userOverrides
      });
      
      const round = response.data as NegotiationRound;
      setCurrentRound(round);
      
      // Refresh terms after round completes
      await getSessionTerms(sessionId);
      
      return round;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to run negotiation round';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, []);

  const getSession = useCallback(async (sessionId: string): Promise<NegotiationSession> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.get(`/api/negotiate/session/${sessionId}`);
      const sessionData = response.data as NegotiationSession;
      setSession(sessionData);
      return sessionData;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to get session';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, []);

  const getSessionTerms = useCallback(async (sessionId: string): Promise<SessionTerm[]> => {
    try {
      const response = await api.get(`/api/negotiate/session/${sessionId}/terms`);
      const termsData = response.data as SessionTerm[];
      setTerms(termsData);
      return termsData;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to get terms';
      setError(errorMsg);
      throw new Error(errorMsg);
    }
  }, []);

  const getSessionRounds = useCallback(async (sessionId: string): Promise<any[]> => {
    try {
      const response = await api.get(`/api/negotiate/session/${sessionId}/rounds`);
      const roundsData = response.data;
      setRounds(roundsData);
      return roundsData;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to get rounds';
      setError(errorMsg);
      throw new Error(errorMsg);
    }
  }, []);

  const updateTerm = useCallback(async (
    sessionId: string,
    clauseKey: string,
    value: TermValue,
    pinnedBy?: string
  ): Promise<SessionTerm> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.put(`/api/negotiate/session/${sessionId}/terms/${clauseKey}`, {
        clause_key: clauseKey,
        value,
        source: 'copilot',
        pinned_by: pinnedBy
      });
      
      const term = response.data as SessionTerm;
      
      // Update local terms
      setTerms(prev => {
        const index = prev.findIndex(t => t.clause_key === clauseKey);
        if (index >= 0) {
          const updated = [...prev];
          updated[index] = term;
          return updated;
        } else {
          return [...prev, term];
        }
      });
      
      return term;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to update term';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, []);

  return {
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
  };
}

