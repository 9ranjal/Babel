import React from 'react'

type Analysis = {
  id: string
  clause_id: string
  band_name?: string | null
  band_score?: number | null
  analysis_json?: {
    posture?: string
    risks?: string[]
    leverage_factors?: string[]
    recommendation?: string
    trades?: any
  } | null
  redraft_text?: string | null
}

export function BatnaCard({ analysis, onRedraft }: { analysis: Analysis; onRedraft: () => void }) {
  return (
    <div className="border rounded p-3 space-y-2">
      <div className="text-xs text-gray-500">Band: {analysis.band_name ?? '—'}</div>
      <div className="text-sm">{analysis.analysis_json?.recommendation ?? '—'}</div>
      <div className="flex gap-2">
        <button className="px-2 py-1 bg-blue-600 text-white rounded" onClick={onRedraft}>
          Redraft
        </button>
      </div>
      {analysis.redraft_text ? (
        <div className="mt-2 text-xs text-gray-600">Redraft ready for overlay.</div>
      ) : null}
    </div>
  )
}


