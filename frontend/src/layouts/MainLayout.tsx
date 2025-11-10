import React, { useState, useEffect } from 'react';

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
  const docId = useDocStore((s) => s.docId);
  const document = useDocStore((s) => s.document);
  const isUploading = useDocStore((s) => s.isUploading);

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

  // Default-collapse when a document is present or upload is in-progress
  useEffect(() => {
    if ((document || isUploading) && !isLeftPanelCollapsed) {
      setIsLeftPanelCollapsed(true);
    }
  }, [document, isUploading, isLeftPanelCollapsed]);

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
            <div className="flex-1 overflow-hidden">
              <div
                className={`h-full grid ${
                  document || isUploading
                    ? isLeftPanelCollapsed
                      ? 'grid-cols-[minmax(360px,1fr)_minmax(520px,1.2fr)]'
                      : 'grid-cols-[minmax(204px,238px)_minmax(360px,1fr)_minmax(520px,1.2fr)]'
                    : isLeftPanelCollapsed
                    ? 'grid-cols-1'
                    : 'grid-cols-[minmax(204px,238px)_minmax(360px,1fr)]'
                }`}
              >
                {!isLeftPanelCollapsed && (
                  <aside className="border-r border-[color:var(--border)] overflow-hidden bg-white/70 backdrop-blur flex flex-col">
                    <ChatHistory onSelectChat={() => {}} currentModule={activeModule} />
                  </aside>
                )}
                <section
                  className={`overflow-hidden main-content-gradient text-neutral-900 ${
                    document || isUploading ? 'border-r border-[color:var(--border)]' : ''
                  }`}
                >
                  <div className="h-full flex flex-col">{children}</div>
                </section>
                {(document || isUploading) ? (
                  <section className="overflow-hidden bg-white/80 backdrop-blur">
                    <ViewerPane key={docId || 'uploading'} />
                  </section>
                ) : null}
              </div>
            </div>
          </ChatSessionsProvider>
        </div>
      </ChatFoldersProvider>
    </ToastProvider>
  );
}
