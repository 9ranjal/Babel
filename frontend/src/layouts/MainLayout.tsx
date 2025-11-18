import React, { useState, useEffect, useRef } from 'react';

import ChatHistory from '../components/ChatHistory';
import TopBarCenter from '../components/TopBarCenter';
import TopBarLeft from '../components/TopBarLeft';
import TopBarRight from '../components/TopBarRight';
import { ToastProvider } from '../hooks/useToast';
import { ChatFoldersProvider } from '../hooks/useChatFolders';
import { ChatSessionsProvider } from '../hooks/ChatSessionsContext';
import { ViewerPane } from '../components/Viewer/ViewerPane';
import { useDocStore } from '../lib/store';

interface MainLayoutProps {
  children: React.ReactNode;
  activeModule?: string;
}

export default function MainLayout({ children, activeModule = 'search' }: MainLayoutProps) {
  const [viewportHeight, setViewportHeight] = useState<number>(0);
  const [devicePixelRatio, setDevicePixelRatio] = useState<number>(1);
  const [browserZoom, setBrowserZoom] = useState<number>(1);
  const [isLeftPanelCollapsed, setIsLeftPanelCollapsed] = useState(true);
  const [hasAutoCollapsedForDoc, setHasAutoCollapsedForDoc] = useState(false);
  const docId = useDocStore((s) => s.docId);
  const doc = useDocStore((s) => s.document);
  const resetStore = useDocStore((s) => s.reset);
  const isUploading = useDocStore((s) => s.isUploading);

  const notifyLayoutChange = () => {
    try {
      document.dispatchEvent(new Event('ui:layoutChanged'));
    } catch {}
  };
  // Resizable split between Copilot (chat) and Graph viewer
  const [viewerRatio, setViewerRatio] = useState<number>(0.75); // 75% graph by default
  const [isViewerOpen, setIsViewerOpen] = useState<boolean>(true);
  const [isChatOpen, setIsChatOpen] = useState<boolean>(true);
  const gridRef = useRef<HTMLDivElement>(null);
  const [dragging, setDragging] = useState<boolean>(false);

  const toggleLeftPanel = () => {
    setIsLeftPanelCollapsed(!isLeftPanelCollapsed);
  };

  // Responsive auto-collapse/expand on resize
  useEffect(() => {
    const handleResize = () => {
      const w = window.innerWidth;
      const collapseBothBelow = 1024; // < lg

      if (w < collapseBothBelow) {
        setIsLeftPanelCollapsed(true);
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Default-collapse once when a document is present or upload is in-progress, but allow manual re-open
  useEffect(() => {
    const hasDocOrUploading = Boolean(doc || isUploading);
    if (hasDocOrUploading && !isLeftPanelCollapsed && !hasAutoCollapsedForDoc) {
      setIsLeftPanelCollapsed(true);
      setHasAutoCollapsedForDoc(true);
    }
    if (!hasDocOrUploading && hasAutoCollapsedForDoc) {
      setHasAutoCollapsedForDoc(false);
    }
  }, [doc, isUploading, isLeftPanelCollapsed, hasAutoCollapsedForDoc]);

  // Simple viewport height tracking
  useEffect(() => {
    const updateViewportMetrics = () => {
      const vh = window.innerHeight;
      const dpr = window.devicePixelRatio || 1;
      const zoom = Math.round((window.outerWidth / window.innerWidth) * 100) / 100;
      
      setViewportHeight(vh);
      setDevicePixelRatio(dpr);
      setBrowserZoom(zoom);
    };

    updateViewportMetrics();
    window.addEventListener('resize', updateViewportMetrics);
    window.addEventListener('orientationchange', updateViewportMetrics);

    return () => {
      window.removeEventListener('resize', updateViewportMetrics);
      window.removeEventListener('orientationchange', updateViewportMetrics);
    };
  }, []);

  // Mouse handlers for resizing
  useEffect(() => {
    const onMouseMove = (e: MouseEvent) => {
      if (!dragging || !gridRef.current) return;
      const rect = gridRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      // When left sidebar is visible, the first column is fixed; compute relative to container
      const ratio = Math.min(0.9, Math.max(0.3, 1 - x / rect.width));
      setViewerRatio(ratio);
    };
    const onMouseUp = () => setDragging(false);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };
  }, [dragging]);

  // Persist open state and ratio across refreshes
  useEffect(() => {
    try {
      const savedOpen = localStorage.getItem('viewerOpen');
      const savedRatio = localStorage.getItem('viewerRatio');
      const savedChat = localStorage.getItem('chatOpen');
      if (savedOpen !== null) setIsViewerOpen(savedOpen === 'true');
      if (savedChat !== null) setIsChatOpen(savedChat === 'true');
      if (savedRatio !== null) {
        const r = parseFloat(savedRatio);
        if (!isNaN(r) && r > 0.2 && r < 0.9) setViewerRatio(r);
      }
    } catch {}
  }, []);
  useEffect(() => {
    try { localStorage.setItem('viewerOpen', String(isViewerOpen)); } catch {}
  }, [isViewerOpen]);
  useEffect(() => {
    try { localStorage.setItem('viewerRatio', String(viewerRatio)); } catch {}
  }, [viewerRatio]);
  useEffect(() => {
    try { localStorage.setItem('chatOpen', String(isChatOpen)); } catch {}
  }, [isChatOpen]);

  // Listen for UI event to show chat (e.g., graph node click)
  useEffect(() => {
    const onShowChat = () => setIsChatOpen(true);
    document.addEventListener('ui:showChat', onShowChat as EventListener);
    return () => document.removeEventListener('ui:showChat', onShowChat as EventListener);
  }, []);

  return (
    <ToastProvider>
      <ChatFoldersProvider>
        <div 
          className="flex flex-col copilot-ambient-bg text-neutral-900 relative main-layout-container"
          style={{ 
            width: '100vw',
            height: viewportHeight > 0 ? `${viewportHeight}px` : '100vh',
            minHeight: viewportHeight > 0 ? `${viewportHeight}px` : '100vh',
            '--viewport-height': viewportHeight > 0 ? `${viewportHeight}px` : '100vh',
            '--device-pixel-ratio': devicePixelRatio,
            '--browser-zoom': browserZoom
          } as React.CSSProperties}
        >
          {/* Top bar with modular components */}
          <ChatSessionsProvider>
            <div className="w-full h-[40px] md:h-[40px] flex items-center overflow-visible backdrop-blur-md border-b border-[color:var(--border)] topbar-gradient">
              <TopBarRight 
                isLeftPanelCollapsed={isLeftPanelCollapsed}
                toggleLeftPanel={toggleLeftPanel}
                activeModule={activeModule}
              />
              <TopBarCenter />
              <TopBarLeft 
                isLeftPanelCollapsed={isLeftPanelCollapsed}
                toggleLeftPanel={toggleLeftPanel}
                activeModule={activeModule}
              />
            </div>
            
            {/* Main Layout: History + Chat + Viewer */}
            <div className="flex-1 overflow-hidden relative">
              <div
                ref={gridRef}
                className="h-full grid"
                style={{
                  gridTemplateColumns: (() => {
                    // Left sidebar accounted for by CSS only; here we set the remaining columns
                    if (isViewerOpen && isChatOpen) {
                      return isLeftPanelCollapsed
                        ? `${Math.round((1 - viewerRatio) * 100)}% ${Math.round(viewerRatio * 100)}%`
                        : `minmax(204px,238px) ${Math.round((1 - viewerRatio) * 100)}% ${Math.round(viewerRatio * 100)}%`;
                    }
                    if (isViewerOpen && !isChatOpen) {
                      return isLeftPanelCollapsed ? `100%` : `minmax(204px,238px) 1fr`;
                    }
                    if (!isViewerOpen && isChatOpen) {
                      return isLeftPanelCollapsed ? `100%` : `minmax(204px,238px) 1fr`;
                    }
                    return undefined;
                  })()
                }}
              >
                {!isLeftPanelCollapsed && (
                  <aside className="border-r border-[color:var(--border)] overflow-hidden bg-white/70 backdrop-blur flex flex-col">
                    <ChatHistory onSelectChat={() => {}} currentModule={activeModule} />
                  </aside>
                )}
                {isChatOpen && (
                <section
                  className={`overflow-hidden main-content-gradient text-neutral-900 ${
                    isViewerOpen ? 'border-r border-[color:var(--border)]' : ''
                  }`}
                  style={{ position: 'relative' }}
                >
                  <div className="h-full flex flex-col">{children}</div>
                  {isViewerOpen && (
                    <div
                      onMouseDown={() => setDragging(true)}
                      className="absolute top-0 -right-0.5 h-full w-1 bg-[color:var(--border)] hover:bg-neutral-600 cursor-col-resize transition-colors"
                      style={{ zIndex: 20 }}
                    />
                  )}
                  {/* Chat-specific hide control removed; use global controls top-right */}
                  {/* Chat-specific 'Show Graph' tab removed; use global controls top-right */}
                </section>
                )}
                {isViewerOpen ? (
                  <section className="overflow-hidden bg-white/80 backdrop-blur relative">
                    <ViewerPane key={docId || 'uploading'} />
                  </section>
                ) : null}
              </div>

              {/* Persistent Global Controls: always visible even if both panes are hidden */}
              <div
                className="absolute top-2 right-2 z-30 flex items-center gap-2"
                style={{ pointerEvents: 'auto' }}
              >
                <button
                  onClick={() => {
                    resetStore();
                    notifyLayoutChange();
                  }}
                  className="text-xs px-2 py-1 bg-white/90 border border-[color:var(--border)] rounded shadow-sm hover:bg-white"
                  aria-label="Clear graph"
                >
                  Clear Graph
                </button>
                <button
                  onClick={() => {
                    setIsChatOpen((v) => !v);
                    requestAnimationFrame(() => notifyLayoutChange());
                  }}
                  className="text-xs px-2 py-1 bg-white/90 border border-[color:var(--border)] rounded shadow-sm hover:bg-white"
                  aria-label={isChatOpen ? 'Hide chat' : 'Show chat'}
                >
                  {isChatOpen ? 'Hide Chat' : 'Show Chat'}
                </button>
                <button
                  onClick={() => {
                    setIsViewerOpen((v) => !v);
                    requestAnimationFrame(() => notifyLayoutChange());
                  }}
                  className="text-xs px-2 py-1 bg-white/90 border border-[color:var(--border)] rounded shadow-sm hover:bg-white"
                  aria-label={isViewerOpen ? 'Hide graph' : 'Show graph'}
                >
                  {isViewerOpen ? 'Hide Graph' : 'Show Graph'}
                </button>
              </div>
            </div>
          </ChatSessionsProvider>
        </div>
      </ChatFoldersProvider>
    </ToastProvider>
  );
}
