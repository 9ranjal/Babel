import React, { useState } from 'react';

import { useDocStore } from '../../lib/store';
import { Button } from '../ui/Button';
import { ClauseList } from './ClauseList';
import { GraphViewer } from './GraphViewer';
import { ParsingStatusTracker } from './ParsingStatusTracker';
import { analyzeClauseInChat } from '../../lib/copilot';
import TermSheetGenerator from '../TermSheetGenerator';

export function ViewerPane() {
  const document = useDocStore((s) => s.document);
  const clauses = useDocStore((s) => s.clauses);
  const selectedClauseId = useDocStore((s) => s.selectedClauseId);
  const isUploading = useDocStore((s) => s.isUploading);
  const parsingStatus = useDocStore((s) => s.parsingStatus);
  const setSelected = useDocStore((s) => s.setSelected);
  const resetStore = useDocStore((s) => s.reset);

  const handleClear = () => {
    resetStore();
  };

  const [viewMode, setViewMode] = useState<'graph' | 'term-sheet'>('graph');

  const handleViewToggle = (mode: 'graph' | 'term-sheet') => {
    setViewMode(mode);
  };

  // Show parsing status tracker when uploading/parsing and no graph yet
  if ((isUploading || parsingStatus) && !document?.graph_json) {
    return <ParsingStatusTracker status={parsingStatus} />;
  }

  if (!document) {
    return (
      <div className="h-full grid grid-rows-[auto_1fr]">
        <div className="flex items-center justify-between border-b bg-white/70 backdrop-blur px-4 py-2">
          <div className="flex items-center gap-2">
            <Button
              variant={viewMode === 'graph' ? 'default' : 'outline'}
              size="sm"
              onClick={() => handleViewToggle('graph')}
              className="text-xs"
            >
              Graph
            </Button>
            <Button
              variant={viewMode === 'term-sheet' ? 'default' : 'outline'}
              size="sm"
              onClick={() => handleViewToggle('term-sheet')}
              className="text-xs"
            >
              Term Sheet Generator
            </Button>
          </div>
        </div>
        <main className="overflow-hidden h-full min-h-0">
          {viewMode === 'term-sheet' ? (
            <TermSheetGenerator />
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-center p-8 gap-4">
              <div className="text-lg font-medium text-[color:var(--ink-700)]">Upload a term sheet to begin</div>
              <div className="text-sm text-[color:var(--ink-500)] max-w-sm">
                Document and graph previews will appear here once you upload a term sheet in the chat.
              </div>
            </div>
          )}
        </main>
      </div>
    );
  }

  return (
    <div className="h-full grid grid-rows-[auto_1fr]">
      <div className="flex items-center justify-between border-b bg-white/70 backdrop-blur px-4 py-2">
        <div className="flex items-center gap-2">
          <Button
            variant={viewMode === 'graph' ? 'default' : 'outline'}
            size="sm"
            onClick={() => handleViewToggle('graph')}
            className="text-xs"
          >
            Graph
          </Button>
          <Button
            variant={viewMode === 'term-sheet' ? 'default' : 'outline'}
            size="sm"
            onClick={() => handleViewToggle('term-sheet')}
            className="text-xs"
          >
            Term Sheet Generator
          </Button>
        </div>
        <Button variant="ghost" size="sm" onClick={handleClear} className="text-xs">
          Clear
        </Button>
      </div>
      <main className="overflow-auto h-full min-h-0">
        {viewMode === 'term-sheet' ? (
          <div className="h-full flex flex-col">
            <TermSheetGenerator />
          </div>
        ) : (
          <GraphViewer
            graphJson={document?.graph_json}
            onSelectClause={(id) => {
              if (id) {
                setSelected(id);
                analyzeClauseInChat(id).catch(() => {
                  // swallow chat errors to avoid breaking UI
                });
              }
            }}
          />
        )}
      </main>
    </div>
  );
}
