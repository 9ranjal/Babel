import React, { useState } from 'react';

import { useDocStore } from '../../lib/store';
import { Button } from '../ui/Button';
import { ClauseList } from './ClauseList';
import { GraphViewer } from './GraphViewer';
import { analyzeClauseInChat } from '../../lib/copilot';

export function ViewerPane() {
  const document = useDocStore((s) => s.document);
  const clauses = useDocStore((s) => s.clauses);
  const selectedClauseId = useDocStore((s) => s.selectedClauseId);
  const isUploading = useDocStore((s) => s.isUploading);
  const setSelected = useDocStore((s) => s.setSelected);
  const resetStore = useDocStore((s) => s.reset);

  const handleClear = () => {
    resetStore();
  };

  if (isUploading && !document) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-center p-8 gap-4">
        <div className="flex flex-col items-center gap-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[color:var(--ink-700)]"></div>
          <div className="text-lg font-medium text-[color:var(--ink-700)]">Processing document...</div>
          <div className="text-sm text-[color:var(--ink-500)] max-w-sm">
            Parsing term sheet and extracting clauses. This may take a few moments.
          </div>
        </div>
      </div>
    );
  }

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
        <div />
        <Button variant="ghost" size="sm" onClick={handleClear} className="text-xs">
          Clear
        </Button>
      </div>
      <main className="overflow-auto h-full min-h-0">
        <GraphViewer
          graphJson={document?.graph_json}
          onSelectClause={(id) => {
            if (id) {
              setSelected(id);
              // Trigger AI analysis in chat
              analyzeClauseInChat(id).catch(() => {
                // swallow chat errors to avoid breaking UI
              });
            }
          }}
        />
      </main>
    </div>
  );
}
