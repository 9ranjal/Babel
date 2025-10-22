/**
 * NegotiationPanel Component
 * 
 * Displays negotiation results including:
 * - Final terms
 * - Per-clause traces with company/investor proposals
 * - Citations (embedded snippets)
 * - Utility scores
 */
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { Alert, AlertDescription } from './ui/alert';
import { CheckCircle2, XCircle, TrendingUp, FileText } from 'lucide-react';
import type { NegotiationRound, NegotiationTrace, EmbeddedSnippet } from '../hooks/useNegotiation';

interface NegotiationPanelProps {
  round: NegotiationRound | null;
  loading?: boolean;
}

export function NegotiationPanel({ round, loading }: NegotiationPanelProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Negotiation in Progress...</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!round) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Negotiation Results</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-500">Run a negotiation round to see results</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header with utilities and status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Round {round.round_no} Summary</span>
            {round.grades?.policy_ok ? (
              <Badge variant="default" className="flex items-center gap-1">
                <CheckCircle2 className="h-4 w-4" />
                Policy Compliant
              </Badge>
            ) : (
              <Badge variant="destructive" className="flex items-center gap-1">
                <XCircle className="h-4 w-4" />
                Policy Issues
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-blue-500" />
              <div>
                <div className="text-sm text-gray-500">Company Utility</div>
                <div className="text-2xl font-bold">{round.utilities.company.toFixed(1)}/100</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-green-500" />
              <div>
                <div className="text-sm text-gray-500">Investor Utility</div>
                <div className="text-2xl font-bold">{round.utilities.investor.toFixed(1)}/100</div>
              </div>
            </div>
          </div>
          
          {round.grades && (
            <div className="text-sm">
              <span className="text-gray-600">Grounding Score: </span>
              <span className="font-semibold">{(round.grades.grounding * 100).toFixed(0)}%</span>
            </div>
          )}
          
          {round.grades?.validation_errors && round.grades.validation_errors.length > 0 && (
            <Alert variant="destructive" className="mt-4">
              <AlertDescription>
                <ul className="list-disc list-inside">
                  {round.grades.validation_errors.map((err, i) => (
                    <li key={i}>{err}</li>
                  ))}
                </ul>
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Per-clause traces */}
      <Card>
        <CardHeader>
          <CardTitle>Term-by-Term Analysis</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {round.traces.map((trace) => (
            <TraceCard key={trace.clause_key} trace={trace} />
          ))}
        </CardContent>
      </Card>

      {/* Citations */}
      {round.citations && round.citations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Citations & References
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {round.citations.map((snippet) => (
                <CitationCard key={snippet.id} snippet={snippet} />
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Full rationale */}
      <Card>
        <CardHeader>
          <CardTitle>Detailed Rationale</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="prose prose-sm max-w-none">
            <pre className="whitespace-pre-wrap font-sans text-sm">
              {round.rationale_md}
            </pre>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function TraceCard({ trace }: { trace: NegotiationTrace }) {
  return (
    <div className="border rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="font-semibold text-lg capitalize">
          {trace.clause_key.replace(/_/g, ' ')}
        </h4>
        <Badge variant="outline">
          {(trace.confidence * 100).toFixed(0)}% confidence
        </Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
        <div className="bg-blue-50 p-3 rounded">
          <div className="font-medium text-blue-900 mb-1">Company Proposal</div>
          <code className="text-xs">{JSON.stringify(trace.company_proposal, null, 2)}</code>
        </div>
        
        <div className="bg-green-50 p-3 rounded">
          <div className="font-medium text-green-900 mb-1">Investor Proposal</div>
          <code className="text-xs">{JSON.stringify(trace.investor_proposal, null, 2)}</code>
        </div>
      </div>

      <div className="bg-purple-50 p-3 rounded">
        <div className="font-medium text-purple-900 mb-1">Final Agreement</div>
        <code className="text-sm font-semibold">{JSON.stringify(trace.final_value, null, 2)}</code>
      </div>

      <Separator />

      <div className="text-sm text-gray-700">
        <span className="font-medium">Rationale: </span>
        {trace.rationale}
      </div>
    </div>
  );
}

function CitationCard({ snippet }: { snippet: EmbeddedSnippet }) {
  const perspectiveColors: Record<string, string> = {
    detail: 'bg-gray-100 text-gray-800',
    founder: 'bg-blue-100 text-blue-800',
    investor: 'bg-green-100 text-green-800',
    batna: 'bg-yellow-100 text-yellow-800',
    balance: 'bg-purple-100 text-purple-800'
  };

  return (
    <div className="border-l-4 border-gray-300 pl-4 py-2">
      <div className="flex items-center gap-2 mb-1">
        <Badge variant="outline" className={perspectiveColors[snippet.perspective] || 'bg-gray-100'}>
          {snippet.perspective}
        </Badge>
        <span className="text-xs text-gray-500">
          {snippet.clause_key} • {snippet.stage} • {snippet.region}
        </span>
      </div>
      <p className="text-sm text-gray-700">{snippet.content}</p>
    </div>
  );
}

