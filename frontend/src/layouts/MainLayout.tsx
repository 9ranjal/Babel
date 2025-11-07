import React, { useState, useEffect } from 'react';

import ResizableLayout2Column from '../components/ResizableLayout2Column';
import TopBarCenter from '../components/TopBarCenter';
import TopBarLeft from '../components/TopBarLeft';
import TopBarRight from '../components/TopBarRight';
import ChatHistory from '../components/ChatHistory';
import { ToastProvider } from '../hooks/useToast';
import { ChatFoldersProvider } from '../hooks/useChatFolders';
import { ChatSessionsProvider } from '../hooks/ChatSessionsContext';

interface MainLayoutProps {
  children: React.ReactNode;
  activeModule?: string;
}

export default function MainLayout({ children, activeModule = 'search' }: MainLayoutProps) {
  const [viewportHeight, setViewportHeight] = useState<number>(0);
  const [devicePixelRatio, setDevicePixelRatio] = useState<number>(1);
  const [browserZoom, setBrowserZoom] = useState<number>(1);
  const [isLeftPanelCollapsed, setIsLeftPanelCollapsed] = useState(false);

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
            
            {/* Main Layout: 2-Column Resizable Layout */}
            <div className="flex-1 overflow-hidden">
              <ResizableLayout2Column
                leftPanel={
                  <ChatHistory 
                    onSelectChat={() => {}}
                    currentModule={activeModule}
                  />
                }
                mainContent={
                  <main className="flex-1 flex flex-col h-full overflow-hidden main-content-gradient min-h-0 text-neutral-900">
                    {children}
                  </main>
                }
                isLeftPanelCollapsed={isLeftPanelCollapsed}
                toggleLeftPanel={toggleLeftPanel}
                activeModule={activeModule}
              />
            </div>
          </ChatSessionsProvider>
        </div>
      </ChatFoldersProvider>
    </ToastProvider>
  );
}
