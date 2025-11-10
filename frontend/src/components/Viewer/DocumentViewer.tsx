import React, { useEffect, useMemo, useRef } from 'react';

import { Button } from '../ui/Button';
import { useDocStore } from '../../lib/store';
import { getRedlineMarkup } from '../../packages/diff/redline';
// Analysis panel removed; AI analysis now appears in chat

type SpanMap = Record<
  string,
  {
    spanId?: string;
  }
>;

interface DocumentViewerProps {
  pagesJson?: unknown;
  spans?: SpanMap;
  selectedClauseId?: string;
}

export function DocumentViewer({ pagesJson, spans, selectedClauseId }: DocumentViewerProps) {
  const analyses = useDocStore((s) => s.analyses);
  const containerRef = useRef<HTMLDivElement>(null);

  const effectiveSpans = useMemo(() => {
    if (spans && Object.keys(spans).length > 0) {
      return spans;
    }
    if (!pagesJson || Array.isArray(pagesJson)) {
      return undefined;
    }
    if (typeof pagesJson === 'object' && pagesJson !== null && 'spans' in pagesJson) {
      return (pagesJson as { spans?: SpanMap }).spans;
    }
    return undefined;
  }, [pagesJson, spans]);

  useEffect(() => {
    if (!selectedClauseId || !effectiveSpans) return;
    const info = effectiveSpans[selectedClauseId];
    if (!info?.spanId) return;
    const node = containerRef.current?.querySelector<HTMLElement>(`#${CSS.escape(info.spanId)}`);
    if (!node) return;

    node.scrollIntoView({ behavior: 'smooth', block: 'center' });
    node.classList.add('ring-2', 'ring-[color:var(--brand)]');
    const timeout = window.setTimeout(() => {
      node.classList.remove('ring-2', 'ring-[color:var(--brand)]');
    }, 1200);

    return () => {
      window.clearTimeout(timeout);
      node.classList.remove('ring-2', 'ring-[color:var(--brand)]');
    };
  }, [selectedClauseId, effectiveSpans]);

  const redraft = useMemo(() => analyses?.[selectedClauseId ?? '']?.redraft_text, [analyses, selectedClauseId]);

  const handleCopyRedraft = () => {
    if (!redraft) return;
    navigator.clipboard?.writeText(redraft).catch(() => {
      // swallow clipboard errors
    });
  };

  const normalizedPages = useMemo(() => {
    const source = (() => {
      if (!pagesJson) return [];
      if (Array.isArray(pagesJson)) return pagesJson;
      if (Array.isArray((pagesJson as any)?.html_pages)) return (pagesJson as any).html_pages;
      if (Array.isArray((pagesJson as any)?.pages)) return (pagesJson as any).pages;
      return [];
    })();

    return source
      .map((page, idx) => {
        if (!page) return null;
        if (typeof page === 'string') {
          return { key: idx, html: page };
        }
        if (typeof page === 'object') {
          const candidateHtml =
            typeof (page as any).html === 'string'
              ? (page as any).html
              : typeof (page as any).content === 'string'
              ? (page as any).content
              : typeof (page as any).markup === 'string'
              ? (page as any).markup
              : null;
          if (!candidateHtml) return null;
          return { key: (page as any).index ?? (page as any).page ?? idx, html: candidateHtml };
        }
        return null;
      })
      .filter(Boolean) as { key: number | string; html: string }[];
  }, [pagesJson]);

  const hasHtml = normalizedPages.length > 0;

  return (
    <div ref={containerRef} className="prose max-w-none p-6 space-y-8">
      {hasHtml ? (
        normalizedPages.map((page) => (
          <div key={page.key} dangerouslySetInnerHTML={{ __html: page.html }} />
        ))
      ) : (
        <div className="p-4 border border-dashed border-[rgba(131,139,148,0.35)] rounded text-sm text-[color:var(--ink-500)] bg-[rgba(247,243,237,0.6)]">
          No HTML extracted. Try re-uploading or a different file.
        </div>
      )}

      {redraft ? (
        <FloatingPanel title="Redraft">
          <div
            className="prose-sm max-w-none"
            dangerouslySetInnerHTML={{ __html: getRedlineMarkup(effectiveSpans, selectedClauseId, redraft) }}
          />
          <Button variant="secondary" size="sm" className="mt-3" onClick={handleCopyRedraft}>
            Copy redraft
          </Button>
        </FloatingPanel>
      ) : null}
    </div>
  );
}

function FloatingPanel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-[color:var(--border)] bg-white shadow-sm overflow-hidden">
      <div className="border-b border-[color:var(--border)] px-4 py-2 text-sm font-medium text-[color:var(--ink-700)]">
        {title}
      </div>
      <div className="px-4 py-3 space-y-3">{children}</div>
    </div>
  );
}

