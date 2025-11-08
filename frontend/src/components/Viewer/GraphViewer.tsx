import React from 'react';

type GraphNode = {
  data?: {
    id?: string;
    label?: string;
    clauseId?: string;
  };
};

type GraphJson = {
  nodes?: GraphNode[];
  edges?: any[];
};

interface GraphViewerProps {
  graphJson?: GraphJson;
  onSelectClause: (clauseId: string) => void;
}

export function GraphViewer({ graphJson, onSelectClause }: GraphViewerProps) {
  if (!graphJson?.nodes || graphJson.nodes.length === 0) {
    return <div className="p-4 text-sm text-[color:var(--ink-500)]">No graph yet.</div>;
  }

  const clauseNodes = graphJson.nodes.filter((node) => node.data?.clauseId);

  if (clauseNodes.length === 0) {
    return <div className="p-4 text-sm text-[color:var(--ink-500)]">No clause nodes available.</div>;
  }

  return (
    <div className="p-4 space-y-2">
      <div className="text-sm font-medium text-[color:var(--ink-500)]">Clauses</div>
      <ul className="space-y-1">
        {clauseNodes.map((node) => {
          const clauseId = node.data?.clauseId;
          if (!clauseId) return null;
          return (
            <li key={node.data?.id || clauseId}>
              <button
                className="text-[#4689F0] hover:underline text-sm"
                onClick={() => onSelectClause(clauseId)}
              >
                {node.data?.label || clauseId}
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
