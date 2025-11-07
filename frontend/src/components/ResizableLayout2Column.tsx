import React, { useState, useRef, useEffect } from 'react';

interface ResizableLayout2ColumnProps {
  leftPanel: React.ReactNode;
  mainContent: React.ReactNode;
  isLeftPanelCollapsed: boolean;
  toggleLeftPanel: () => void;
  activeModule?: string;
}

export const ResizableLayout2Column: React.FC<ResizableLayout2ColumnProps> = ({
  leftPanel,
  mainContent,
  isLeftPanelCollapsed,
  toggleLeftPanel,
  activeModule
}) => {
  // Calculate initial left width based on active module
  const baseLeftWidth = 250;
  const isMainModule = activeModule === 'aanaeai' || activeModule === 'explore' || activeModule === 'search';
  const initialLeftWidth = isMainModule
    ? baseLeftWidth
    : Math.round(baseLeftWidth * 1.2);
  
  const [leftWidth, setLeftWidth] = useState(initialLeftWidth);
  const [isDraggingLeft, setIsDraggingLeft] = useState(false);
  
  const leftResizerRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Mobile detection for overlay sidebars
  const [isMobile, setIsMobile] = useState(false);
  useEffect(() => {
    const handleMedia = () => {
      try {
        const mobile = window.innerWidth < 768;
        setIsMobile(mobile);
      } catch (_) {
        setIsMobile(false);
      }
    };
    handleMedia();
    window.addEventListener('resize', handleMedia);
    return () => window.removeEventListener('resize', handleMedia);
  }, [isLeftPanelCollapsed]);

  // Calculate left panel width constraints
  const baseMinLeftWidth = 250;
  const baseMaxLeftWidth = 350;
  
  const minLeftWidthMultiplier = isMainModule ? 0.95 : 1.2;
  const maxLeftWidthMultiplier = isMainModule ? 1 : 1.2;
  
  const MIN_LEFT_WIDTH = Math.round(baseMinLeftWidth * minLeftWidthMultiplier);
  const MAX_LEFT_WIDTH = Math.round(baseMaxLeftWidth * maxLeftWidthMultiplier);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!containerRef.current) return;

      const containerRect = containerRef.current.getBoundingClientRect();

      if (isDraggingLeft) {
        const newLeftWidth = Math.max(MIN_LEFT_WIDTH, Math.min(MAX_LEFT_WIDTH, e.clientX - containerRect.left));
        setLeftWidth(newLeftWidth);
      }
    };

    const handleMouseUp = () => {
      setIsDraggingLeft(false);
      document.body.style.userSelect = '';
      document.body.style.cursor = '';
    };

    if (isDraggingLeft) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.userSelect = 'none';
      document.body.style.cursor = 'col-resize';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.userSelect = '';
      document.body.style.cursor = '';
    };
  }, [isDraggingLeft, MIN_LEFT_WIDTH, MAX_LEFT_WIDTH]);

  // Update left width when activeModule changes
  useEffect(() => {
    const baseLeftWidth = 250;
    const isMainNow = activeModule === 'aanaeai' || activeModule === 'explore' || activeModule === 'search';
    const newLeftWidth = isMainNow
      ? Math.round(baseLeftWidth * 0.95)
      : Math.round(baseLeftWidth * 1.2);
    
    if (Math.abs(leftWidth - newLeftWidth) > 5) {
      setLeftWidth(newLeftWidth);
    }
  }, [activeModule, leftWidth]);

  // Update top bar border when sidebar width changes
  useEffect(() => {
    const leftBorderEvent = new CustomEvent('updateLeftBorder', { detail: { width: leftWidth } });
    document.dispatchEvent(leftBorderEvent);
  }, [leftWidth]);

  const handleLeftResizerMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDraggingLeft(true);
  };

  return (
    <div 
      ref={containerRef}
      className="flex h-full w-full"
      style={{ cursor: isDraggingLeft ? 'col-resize' : 'default' }}
    >
      {/* Mobile overlay for left sidebar */}
      {isMobile && !isLeftPanelCollapsed && (
        <>
          <div 
            className="md:hidden fixed inset-0 top-[48px] bg-black bg-opacity-50 z-40"
            aria-hidden="true"
            onClick={toggleLeftPanel}
          />
          <div className="
            w-[280px] min-w-[280px] max-w-[280px]
            md:w-[230px] md:min-w-[230px] md:max-w-[230px]
            text-neutral-900 flex flex-col
            fixed md:relative
            left-0 top-[48px] md:top-0
            h-[calc(100%-48px)] md:h-full
            z-50 md:z-auto
            bg-[color:var(--panel)] border-r border-[color:var(--border)]
            overflow-y-auto
          ">
            {leftPanel}
          </div>
        </>
      )}

      {/* Left Panel - desktop/tablet only */}
      {!isMobile && !isLeftPanelCollapsed && (
        <>
          <div 
            className="text-neutral-900 flex flex-col bg-[color:var(--panel)] border-r border-[color:var(--border)] relative z-10"
            style={{ width: `${leftWidth}px`, minWidth: `${leftWidth}px`, maxWidth: `${leftWidth}px` }}
          >
            {leftPanel}
          </div>
          
          {/* Left Resizer */}
          <div
            ref={leftResizerRef}
            className="w-px bg-neutral-800 hover:bg-neutral-600 cursor-col-resize transition-colors relative group"
            onMouseDown={handleLeftResizerMouseDown}
            style={{ cursor: 'col-resize', position: 'absolute', left: `${leftWidth}px`, top: 0, bottom: 0, zIndex: 10 }}
          >
            <div className="absolute inset-y-0 -left-2 -right-2 bg-transparent group-hover:bg-neutral-700/10 transition-colors" />
          </div>
        </>
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col h-full min-w-0 bg-transparent">
        <div className="flex-1 overflow-auto w-full h-full bg-transparent">
          {mainContent}
        </div>
      </div>
    </div>
  );
};

export default ResizableLayout2Column;

