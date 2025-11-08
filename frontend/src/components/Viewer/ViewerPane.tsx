import React, { useState } from 'react';

import { useDocStore } from '../../lib/store';
import { Button } from '../ui/Button';
import { ClauseList } from './ClauseList';
import { DocumentViewer } from './DocumentViewer';
import { GraphViewer } from './GraphViewer';

type TabKey = 'doc' | 'graph';

const tabs: { key: TabKey; label: string }[] = [
  { key: 'doc', label: 'Document' },
  { key: 'graph', label: 'Graph' },
];

export function ViewerPane() {
  const document = useDocStore((s) => s.document);
  const clauses = useDocStore((s) => s.clauses);
  const selectedClauseId = useDocStore((s) => s.selectedClauseId);
  const setSelected = useDocStore((s) => s.setSelected);
  const resetStore = useDocStore((s) => s.reset);

  const [tab, setTab] = useState<TabKey>('doc');

  const handleClear = () => {
    setTab('doc');
    resetStore();
  };

  if (!document) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-center p-8 gap-4">
        <div className="text-lg font-medium text-[color:var(--ink-700)]">Upload a term sheet to begin</div>
        <div className="text-sm text-[color:var(--ink-500)] max-w-sm">
          Document and graph previews will appear here once you upload a term sheet in the chat.
        </div>
      </div>
    );
  }

  return (
    <div className="h-full grid grid-rows-[auto_1fr]">
      <div className="flex items-center justify-between border-b bg-white/70 backdrop-blur px-4 py-2">
        <div className="flex gap-1">
          {tabs.map((t) => (
            <TabButton key={t.key} active={tab === t.key} onClick={() => setTab(t.key)}>
              {t.label}
            </TabButton>
          ))}
        </div>
        <Button variant="ghost" size="sm" onClick={handleClear} className="text-xs">
          Clear
        </Button>
      </div>
      <div className="grid grid-cols-[260px_1fr] h-full min-h-0">
        <aside className="border-r border-[color:var(--border)] overflow-auto bg-[rgba(247,243,237,0.5)]">
          <ClauseList clauses={clauses} selectedId={selectedClauseId} onSelect={(id) => setSelected(id)} />
        </aside>
        <main className="overflow-auto">
          {tab === 'doc' ? (
            <DocumentViewer
              pagesJson={document?.pages_json}
              spans={document?.pages_json?.spans || {}}
              selectedClauseId={selectedClauseId}
            />
          ) : (
            <GraphViewer
              graphJson={document?.graph_json}
              onSelectClause={(id) => {
                if (id) {
                  setSelected(id);
                  setTab('doc');
                }
              }}
            />
          )}
        </main>
      </div>
    </div>
  );
}

function TabButton({
  children,
  active,
  onClick,
}: {
  children: React.ReactNode;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
        active
          ? 'bg-[#4689F0] text-white shadow-sm'
          : 'text-[color:var(--ink-500)] hover:bg-[rgba(70,137,240,0.1)]'
      }`}
    >
      {children}
    </button>
  );
}


