export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  ts: number;
  termSheet?: string;
  suggestion?: any;
  isChipMessage?: boolean;
}

export interface ChatSession {
  id: string;
  name: string;
  createdAt: string;
  lastActivity: string;
  messageCount: number;
}

export interface Transaction {
  id: string;
  name: string;
  created_at: string;
  status: string;
}

export interface TermSheetData {
  [key: string]: any;
}

export interface CopilotResponse {
  intent: string;
  success: boolean;
  message: string;
  updated_clauses?: any[];
  utilities?: { [key: string]: number };
  suggested_trades?: string[];
  citations?: any[];
}

