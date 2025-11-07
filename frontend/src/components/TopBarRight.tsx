import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { useChatSessions } from '../hooks/useChatSessions';

interface TopBarRightProps {
  isLeftPanelCollapsed?: boolean;
  toggleLeftPanel?: () => void;
  activeModule?: string;
}

const TopBarRight: React.FC<TopBarRightProps> = ({ 
  isLeftPanelCollapsed = false, 
  toggleLeftPanel = () => {},
  activeModule = 'search'
}) => {
  const baseLeftWidth = 250;
  const initialWidth = Math.round(baseLeftWidth * 0.95);
  const [leftWidth, setLeftWidth] = useState(initialWidth);
  const [showTooltip, setShowTooltip] = useState(false);
  const [tooltipPos, setTooltipPos] = useState({ left: 0, top: 0 });
  const [showAanaeTooltip, setShowAanaeTooltip] = useState(false);
  const [aanaeTooltipPos, setAanaeTooltipPos] = useState({ left: 0, top: 0 });
  const buttonRef = useRef<HTMLButtonElement>(null);
  const aanaeButtonRef = useRef<HTMLButtonElement>(null);
  const { createSession } = useChatSessions();
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  useEffect(() => {
    const handleLeftBorderUpdate = (event: CustomEvent) => {
      setLeftWidth(event.detail.width);
    };

    document.addEventListener('updateLeftBorder', handleLeftBorderUpdate as EventListener);
    
    return () => {
      document.removeEventListener('updateLeftBorder', handleLeftBorderUpdate as EventListener);
    };
  }, []);

  const getFirstButtonLabel = () => {
    return isLeftPanelCollapsed ? 'Show History' : 'History';
  };

  const handleFirstButtonClick = () => {
    toggleLeftPanel();
  };

  const handleNewChat = () => {
    createSession('New conversation', 'search');
  };

  return (
    <div 
      className="flex items-center h-[48px] md:h-[40px] px-2 relative flex-shrink-0"
      style={{ 
        width: isMobile ? 'auto' : `${leftWidth}px`,
        minWidth: isMobile ? 'auto' : `${leftWidth}px`,
        maxWidth: isMobile ? 'none' : `${leftWidth}px`
      }}
    >
      <div className="w-full h-full flex items-center justify-between">
        <div className="flex items-center gap-x-2">
          {(() => {
            const buttonWidth = leftWidth <= 230 ? 76 : 92;
            const sharedStyle: React.CSSProperties = { width: `${buttonWidth}px`, minWidth: `${buttonWidth}px` };
            return (
              <>
                <button
                  ref={buttonRef}
                  onClick={handleFirstButtonClick}
                  onMouseEnter={() => {
                    const rect = buttonRef.current?.getBoundingClientRect();
                    if (rect) {
                      setTooltipPos({
                        left: rect.left + rect.width / 2,
                        top: rect.bottom + 8
                      });
                      setShowTooltip(true);
                    }
                  }}
                  onMouseLeave={() => setShowTooltip(false)}
                  className={`flex items-center justify-center px-2 py-1.5 rounded-[8px] transition-colors border min-h-[36px] text-[13px] md:px-2.5 md:py-1.5 md:rounded-[9px] md:min-h-0 md:text-[11px] relative z-50 touch-manipulation cursor-pointer bg-[color:var(--ink-900)] text-white border-transparent`}
                  style={sharedStyle}
                >
                  <span className="text-[11px] leading-none">
                    {getFirstButtonLabel()}
                  </span>
                </button>

                <div className="md:hidden">
                  <button
                    ref={aanaeButtonRef}
                    onClick={handleNewChat}
                    onMouseEnter={() => {
                      const rect = aanaeButtonRef.current?.getBoundingClientRect();
                      if (rect) {
                        setAanaeTooltipPos({
                          left: rect.left + rect.width / 2,
                          top: rect.bottom + 8
                        });
                        setShowAanaeTooltip(true);
                      }
                    }}
                    onMouseLeave={() => setShowAanaeTooltip(false)}
                    className="flex items-center justify-center hover:bg-neutral-700 rounded-md text-neutral-400 hover:text-white transition-colors border border-neutral-600/50"
                    title="Start new chat"
                    style={{ width: '44px', height: '44px', minWidth: '44px', minHeight: '44px' }}
                  >
                    <img 
                      src="/babel-logo.svg" 
                      alt="Babel Logo" 
                      style={{ width: '32px', height: '32px', maxWidth: '32px', maxHeight: '32px' }}
                    />
                  </button>
                </div>

                {/* Desktop */}
                <div className="hidden md:block">
                  <button
                    ref={aanaeButtonRef}
                    onClick={handleNewChat}
                    onMouseEnter={() => {
                      const rect = aanaeButtonRef.current?.getBoundingClientRect();
                      if (rect) {
                        setAanaeTooltipPos({
                          left: rect.left + rect.width / 2,
                          top: rect.bottom + 8
                        });
                        setShowAanaeTooltip(true);
                      }
                    }}
                    onMouseLeave={() => setShowAanaeTooltip(false)}
                    className="flex items-center justify-center hover:bg-neutral-700 rounded text-neutral-400 hover:text-white transition-colors border border-neutral-600/50"
                    style={{ width: '36px', height: '36px', minWidth: '36px', minHeight: '36px', padding: '2px' }}
                  >
                    <img 
                      src="/babel-logo.svg" 
                      alt="Babel Logo" 
                      style={{ width: '24px', height: '24px', maxWidth: '24px', maxHeight: '24px' }}
                    />
                  </button>
                </div>
              </>
            );
          })()}
        </div>

        <div className="flex items-center">
          {(() => {
            const buttonWidth = leftWidth <= 230 ? 76 : 92;
            return <div style={{ width: `${buttonWidth}px`, minWidth: `${buttonWidth}px` }} />;
          })()}
        </div>
      </div>

      {showTooltip && createPortal(
        <div 
          className="fixed px-3 py-1.5 text-xs text-white bg-gray-900 rounded shadow-lg whitespace-nowrap pointer-events-none z-[999999]"
          style={{ 
            left: `${tooltipPos.left}px`, 
            top: `${tooltipPos.top}px`,
            transform: 'translateX(-50%)'
          }}
        >
          {isLeftPanelCollapsed ? "Show History Panel" : "Hide History Panel"}
          <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-b-4 border-transparent border-b-gray-900"></div>
        </div>,
        document.body
      )}

      {showAanaeTooltip && createPortal(
        <div 
          className="fixed px-3 py-1.5 text-xs text-white bg-gray-900 rounded shadow-lg whitespace-nowrap pointer-events-none z-[999999]"
          style={{ 
            left: `${aanaeTooltipPos.left}px`, 
            top: `${aanaeTooltipPos.top}px`,
            transform: 'translateX(-50%)'
          }}
        >
          Start new chat
          <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-b-4 border-transparent border-b-gray-900"></div>
        </div>,
        document.body
      )}
    </div>
  );
};

export default TopBarRight;

