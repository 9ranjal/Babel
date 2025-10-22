/**
 * TermsDisplay Component
 * 
 * Displays current session terms in a clean, editable format
 */
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Lock, Unlock, Edit2 } from 'lucide-react';
import type { SessionTerm } from '../hooks/useNegotiation';

interface TermsDisplayProps {
  terms: SessionTerm[];
  onEdit?: (clauseKey: string) => void;
  onTogglePin?: (clauseKey: string, currentlyPinned: boolean) => void;
}

export function TermsDisplay({ terms, onEdit, onTogglePin }: TermsDisplayProps) {
  if (terms.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Current Terms</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-500">No terms negotiated yet</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Current Terms</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {terms.map((term) => (
          <TermRow 
            key={term.clause_key} 
            term={term} 
            onEdit={onEdit}
            onTogglePin={onTogglePin}
          />
        ))}
      </CardContent>
    </Card>
  );
}

function TermRow({ 
  term, 
  onEdit, 
  onTogglePin 
}: { 
  term: SessionTerm;
  onEdit?: (clauseKey: string) => void;
  onTogglePin?: (clauseKey: string, currentlyPinned: boolean) => void;
}) {
  const sourceColors: Record<string, string> = {
    rule: 'bg-gray-100 text-gray-800',
    persona: 'bg-blue-100 text-blue-800',
    copilot: 'bg-purple-100 text-purple-800'
  };

  const isPinned = !!term.pinned_by;

  return (
    <div className="border rounded-lg p-3 hover:bg-gray-50 transition-colors">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h4 className="font-medium capitalize">
              {term.clause_key.replace(/_/g, ' ')}
            </h4>
            <Badge variant="outline" className={sourceColors[term.source]}>
              {term.source}
            </Badge>
            {term.confidence && (
              <Badge variant="outline">
                {(term.confidence * 100).toFixed(0)}%
              </Badge>
            )}
          </div>
          
          <div className="text-sm bg-gray-50 p-2 rounded font-mono">
            {JSON.stringify(term.value, null, 2)}
          </div>
          
          {term.pinned_by && (
            <div className="text-xs text-gray-500 mt-1">
              Pinned by: {term.pinned_by}
            </div>
          )}
        </div>

        <div className="flex flex-col gap-1">
          {onTogglePin && (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => onTogglePin(term.clause_key, isPinned)}
              title={isPinned ? 'Unpin term' : 'Pin term'}
            >
              {isPinned ? (
                <Lock className="h-4 w-4 text-orange-500" />
              ) : (
                <Unlock className="h-4 w-4 text-gray-400" />
              )}
            </Button>
          )}
          
          {onEdit && (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => onEdit(term.clause_key)}
              title="Edit term"
            >
              <Edit2 className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

