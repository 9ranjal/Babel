import React from 'react';

type Clause = {
  id: string;
  title?: string;
  clause_key?: string;
};

interface ClauseListProps {
  clauses: Clause[] | undefined;
  selectedId?: string;
  onSelect: (id: string) => void;
}

export function ClauseList({ clauses, selectedId, onSelect }: ClauseListProps) {
  if (!clauses || clauses.length === 0) {
    return <div className="p-4 text-sm text-[color:var(--ink-500)]">No clauses found.</div>;
  }

  return (
    <ul className="divide-y divide-[color:var(--border)]">
      {clauses.map((clause) => (
        <li
          key={clause.id}
          className={`px-3 py-2 cursor-pointer transition-colors ${
            clause.id === selectedId
              ? 'bg-[rgba(70,137,240,0.12)]'
              : 'hover:bg-[rgba(70,137,240,0.08)]'
          }`}
          onClick={() => onSelect(clause.id)}
          title={clause.title || clause.clause_key}
        >
          <div className="text-sm font-medium text-[color:var(--ink-700)]">
            {clause.title || clause.clause_key || 'Clause'}
          </div>
          <div className="text-xs text-[color:var(--ink-500)] truncate">
            {clause.clause_key ?? '—'}
          </div>
        </li>
      ))}
    </ul>
  );
}


