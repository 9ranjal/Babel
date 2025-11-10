import React, { useState } from 'react'
import { analyzeClause } from '../../lib/api'

type Analysis = {
  id: string
  clause_id: string
  posture?: string | null
  band_name?: string | null
  band_score?: number | null
  analysis_json?: {
    posture?: string
    band_name?: string
    band_score?: number
    rationale?: string[]
    recommendation?: string
    trades?: string[]
  } | null
  trades?: string[]
  redraft_text?: string | null
}

function getPostureColor(posture: string | null) {
  switch (posture) {
    case 'founder_friendly':
      return 'bg-green-100 text-green-800 border-green-200'
    case 'market':
      return 'bg-blue-100 text-blue-800 border-blue-200'
    case 'investor_friendly':
      return 'bg-red-100 text-red-800 border-red-200'
    default:
      return 'bg-gray-100 text-gray-800 border-gray-200'
  }
}

export function BatnaCard({
  analysis,
  onRedraft,
  clauseId,
  onAnalysisUpdate
}: {
  analysis: Analysis;
  onRedraft: () => void;
  clauseId: string;
  onAnalysisUpdate: (newAnalysis: Analysis) => void;
}) {
  const [isReasonedLoading, setIsReasonedLoading] = useState(false)
  const posture = analysis.posture || analysis.analysis_json?.posture
  const rationale = analysis.analysis_json?.rationale || []
  const recommendation = analysis.analysis_json?.recommendation
  const trades = analysis.trades || analysis.analysis_json?.trades || []

  const handleReasonedAnalysis = async () => {
    setIsReasonedLoading(true)
    try {
      const newAnalysis = await analyzeClause(clauseId, true)
      onAnalysisUpdate(newAnalysis)
    } catch (error) {
      console.error('Failed to get reasoned analysis:', error)
    } finally {
      setIsReasonedLoading(false)
    }
  }

  return (
    <div className="border rounded-lg p-4 space-y-3 bg-white shadow-sm">
      {/* Header with Band Name and Posture */}
      <div className="flex items-center justify-between">
        <div className="font-medium text-lg">
          Band: {analysis.band_name || 'Unknown'}
        </div>
        <div className={`px-2 py-1 text-xs font-medium rounded border ${getPostureColor(posture)}`}>
          {posture || 'Unknown'}
        </div>
      </div>

      {/* Band Score */}
      {analysis.band_score && (
        <div className="text-sm text-gray-600">
          Score: {analysis.band_score.toFixed(3)}
        </div>
      )}

      {/* AI Analysis (if available) */}
      {recommendation && (
        <div className="space-y-1">
          <div className="text-sm font-medium text-gray-700">AI Analysis:</div>
          <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded whitespace-pre-wrap">
            {recommendation}
          </div>
        </div>
      )}

      {/* Rationale */}
      {rationale.length > 0 && !recommendation && (
        <div className="space-y-1">
          <div className="text-sm font-medium text-gray-700">Rationale:</div>
          <ul className="text-sm text-gray-600 space-y-1">
            {rationale.slice(0, 2).map((item, idx) => (
              <li key={idx} className="flex items-start">
                <span className="mr-2">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Suggested Trades */}
      {trades.length > 0 && (
        <div className="space-y-1">
          <div className="text-sm font-medium text-gray-700">Suggested Trades:</div>
          <ul className="text-sm text-gray-600 space-y-1">
            {trades.map((trade, idx) => (
              <li key={idx} className="flex items-start">
                <span className="mr-2">↔</span>
                <span>{trade}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-2 pt-2">
        {!recommendation && (
          <button
            className="px-3 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm font-medium rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={handleReasonedAnalysis}
            disabled={isReasonedLoading}
          >
            {isReasonedLoading ? 'Analyzing...' : 'AI Analysis'}
          </button>
        )}
        <button
          className="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded transition-colors"
          onClick={onRedraft}
        >
          Redraft
        </button>
      </div>

      {/* Redraft Status */}
      {analysis.redraft_text && (
        <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded">
          Redraft ready for overlay.
        </div>
      )}
    </div>
  )
}


