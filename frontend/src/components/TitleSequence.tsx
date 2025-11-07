import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface TitleSequenceProps {
  onComplete?: () => void;
}

export const TitleSequence: React.FC<TitleSequenceProps> = ({ onComplete }) => {
  const [showTitle, setShowTitle] = useState(false);
  const hasRunRef = useRef(false);

  // Store onComplete callback
  const onCompleteRef = useRef(onComplete);
  useEffect(() => {
    onCompleteRef.current = onComplete;
  }, [onComplete]);

  useEffect(() => {
    console.log('[TitleSequence] useEffect triggered, hasRunRef.current:', hasRunRef.current);
    if (hasRunRef.current) {
      console.log('[TitleSequence] Already ran, returning early');
      return;
    }
    hasRunRef.current = true;

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    console.log('[TitleSequence] prefersReducedMotion:', prefersReducedMotion);
    
    if (prefersReducedMotion) {
      console.log('[TitleSequence] Reduced motion detected, calling onComplete immediately');
      if (onCompleteRef.current) onCompleteRef.current();
      return;
    }

    // Timeline per spec:
    // 1.2s: "Welcome to Babel" fades in (2.86s duration)
    // 4.0s: Fades out (1.56s duration)
    console.log('[TitleSequence] Starting animation at', new Date().toISOString());
    const t1 = setTimeout(() => {
      console.log('[TitleSequence] 1.2s: Showing title');
      setShowTitle(true);
    }, 1200);
    const t2 = setTimeout(() => {
      console.log('[TitleSequence] 4.0s: Fading out, calling onComplete');
      setShowTitle(false);
      onCompleteRef.current?.();
    }, 4000);

    return () => {
      clearTimeout(t1); clearTimeout(t2);
    };
  }, []);


  console.log('[TitleSequence] Render - showTitle:', showTitle);

  return (
    <div
      className="z-10"
      style={{
        position: 'fixed',
        inset: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        pointerEvents: 'none'
      }}
    >
      <div style={{ textAlign: 'center' }}>
        {/* Title container - preserved space */}
        <div style={{ minHeight: '56px', marginBottom: '16px' }}>
          <AnimatePresence mode="wait">
            {showTitle && (
              <motion.h1
                key="title"
              transition={{
                duration: 2.86,
                ease: [0.4, 0, 0.2, 1] 
              }}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                style={{
                  fontSize: '48px',
                  fontWeight: 700,
                  color: '#0E0F14',
                  margin: 0,
                  whiteSpace: 'nowrap'
                }}
              >
                Welcome to Babel
              </motion.h1>
            )}
          </AnimatePresence>
        </div>

      </div>

    </div>
  );
};

