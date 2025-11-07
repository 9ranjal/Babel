import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface TooltipProps {
  content: string;
  children: React.ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
  delay?: number;
  disabled?: boolean;
}

export default function Tooltip({ 
  content, 
  children, 
  position = 'top', 
  delay = 200,
  disabled = false 
}: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });
  const triggerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout>();

  const showTooltip = () => {
    if (disabled || !content) return;
    
    timeoutRef.current = setTimeout(() => {
      if (triggerRef.current) {
        const rect = triggerRef.current.getBoundingClientRect();
        const viewport = {
          width: window.innerWidth,
          height: window.innerHeight
        };
        
        let x = 0;
        let y = 0;
        let adjustedPosition = position;
        
        // Calculate base position
        switch (position) {
          case 'top':
            x = rect.left + rect.width / 2;
            y = rect.top - 8;
            break;
          case 'bottom':
            x = rect.left + rect.width / 2;
            y = rect.bottom + 8;
            break;
          case 'left':
            x = rect.left - 8;
            y = rect.top + rect.height / 2;
            break;
          case 'right':
            x = rect.right + 8;
            y = rect.top + rect.height / 2;
            break;
        }
        
        // Check viewport boundaries and adjust position if needed
        const tooltipWidth = Math.max(120, content.length * 7);
        const tooltipHeight = 32;
        const padding = 16;
        
        // Adjust horizontal position if tooltip would go off-screen
        if (x - tooltipWidth / 2 < padding) {
          x = padding + tooltipWidth / 2;
        } else if (x + tooltipWidth / 2 > viewport.width - padding) {
          x = viewport.width - padding - tooltipWidth / 2;
        }
        
        // Adjust vertical position if tooltip would go off-screen
        if (y - tooltipHeight < padding) {
          if (position === 'top') {
            y = rect.bottom + 8;
            adjustedPosition = 'bottom';
          }
        } else if (y + tooltipHeight > viewport.height - padding) {
          if (position === 'bottom') {
            y = rect.top - 8;
            adjustedPosition = 'top';
          }
        }
        
        setTooltipPosition({ x, y });
        setIsVisible(true);
      }
    }, delay);
  };

  const hideTooltip = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setIsVisible(false);
  };

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const getTooltipClasses = () => {
    const baseClasses = "fixed z-[99999] px-3 py-1.5 text-xs text-white bg-gray-900 rounded shadow-lg whitespace-nowrap pointer-events-none min-w-max";
    
    switch (position) {
      case 'top':
        return `${baseClasses} -translate-x-1/2 -translate-y-full`;
      case 'bottom':
        return `${baseClasses} -translate-x-1/2`;
      case 'left':
        return `${baseClasses} -translate-x-full -translate-y-1/2`;
      case 'right':
        return `${baseClasses} -translate-y-1/2`;
      default:
        return baseClasses;
    }
  };

  return (
    <>
      <div
        ref={triggerRef}
        onMouseEnter={showTooltip}
        onMouseLeave={hideTooltip}
        onFocus={showTooltip}
        onBlur={hideTooltip}
        className="inline-block"
        data-tooltip-wrapper="true"
      >
        {children}
      </div>
      
      <AnimatePresence>
        {isVisible && (
          <motion.div
            ref={tooltipRef}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.15 }}
            className={getTooltipClasses()}
            style={{
              left: tooltipPosition.x,
              top: tooltipPosition.y,
            }}
          >
            {content}
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

