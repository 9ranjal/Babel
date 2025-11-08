import React from 'react'

type GraphJson = { nodes: { data: { id: string; type: string; label: string } }[]; edges: any[] }

export function GraphViewer({ graph, onSelect }: { graph: GraphJson; onSelect: (clauseId: string) => void }) {
  return (
    <div className="p-4">
      <div className="text-sm text-gray-500 mb-2">Graph (list fallback)</div>
      <ul className="space-y-1">
        {graph.nodes
          .filter((n) => n.data.type === 'clause')
          .map((n) => (
            <li key={n.data.id}>
              <button
                className="text-blue-600 hover:underline"
                onClick={() => {
                  const id = n.data.id.replace('clause:', '')
                  onSelect(id)
                }}
              >
                {n.data.label}
              </button>
            </li>
          ))}
      </ul>
    </div>
  )
}


