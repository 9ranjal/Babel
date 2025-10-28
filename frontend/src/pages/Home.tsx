import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { GraphBackground } from '../components/GraphBackground';
import { TitleSequence } from '../components/TitleSequence';
import { LandingCTA } from '../components/LandingCTA';

export default function Home() {
  const [showCTA, setShowCTA] = useState(false);
  const [showGraph, setShowGraph] = useState(false);

  useEffect(() => {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    
    if (prefersReducedMotion) {
      setShowCTA(true);
      return;
    }

    // Timeline per spec:
    // 0.8s: Graph background starts fading in (1.4s duration)
    // CTA at 6s
    const graphTimer = setTimeout(() => {
      setShowGraph(true);
    }, 800);

    // Show CTA buttons after title fully fades out (at 4.0s + 1.56s fade duration + 0.2s buffer = 5.76s)
    const ctaTimer = setTimeout(() => {
      console.log('[Home] Showing CTA buttons at 5.76s');
      setShowCTA(true);
    }, 5760);
    
    console.log('[Home] Timer set for CTA at 5.76s');

    return () => {
      clearTimeout(graphTimer);
      clearTimeout(ctaTimer);
    };
  }, []);

  const handleSequenceComplete = () => {
    // Called after particle burst completes
  };

  return (
    <div className="relative min-h-screen bg-[#F6F1EA] flex items-center justify-center overflow-hidden">
      {/* Graph Background - Show at 5.5s */}
      <AnimatePresence>
        {showGraph && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 1.4, ease: "easeInOut" }}
            className="absolute inset-0 z-0"
          >
            <GraphBackground />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Content */}
      <div className="relative z-10 w-full min-h-screen flex items-center justify-center">
        <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '32px' }}>
          {/* Title Sequence - Fixed centered */}
          <TitleSequence onComplete={handleSequenceComplete} />

          {/* CTA Section - Below title */}
          <AnimatePresence>
            {showCTA && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 1.2, ease: [0.4, 0, 0.2, 1] }}
              >
                <LandingCTA />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
