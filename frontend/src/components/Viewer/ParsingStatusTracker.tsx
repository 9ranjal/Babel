import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FileText, Search, Network, CheckCircle2, Loader2 } from 'lucide-react';

type ParsingStatus = 'uploaded' | 'extracted' | 'graphed' | 'analyzed' | null;

interface ParsingStatusTrackerProps {
  status: ParsingStatus;
}

const STAGES: Array<{ key: ParsingStatus; label: string; description: string; icon: React.ReactNode }> = [
  {
    key: 'uploaded',
    label: 'Uploading',
    description: 'Document received and queued for processing',
    icon: <FileText className="w-5 h-5" />
  },
  {
    key: 'extracted',
    label: 'Extracting',
    description: 'Parsing document and extracting clauses',
    icon: <Search className="w-5 h-5" />
  },
  {
    key: 'graphed',
    label: 'Building Graph',
    description: 'Creating relationship graph between clauses',
    icon: <Network className="w-5 h-5" />
  },
  {
    key: 'analyzed',
    label: 'Analyzing',
    description: 'Finalizing analysis and preparing visualization',
    icon: <CheckCircle2 className="w-5 h-5" />
  }
];

export function ParsingStatusTracker({ status }: ParsingStatusTrackerProps) {
  // If status is null but component is shown, assume we're at the first stage
  const effectiveStatus = status || 'uploaded';
  const currentStageIndex = STAGES.findIndex(s => s.key === effectiveStatus);
  const activeStage = STAGES.find(s => s.key === effectiveStatus) || STAGES[0];

  return (
    <div className="h-full w-full flex flex-col items-center justify-center p-8 gap-8" style={{ background: '#F9F6F0' }}>
      <div className="flex flex-col items-center gap-6 max-w-md w-full">
        {/* Main Status Display */}
        <AnimatePresence mode="wait">
          <motion.div
            key={effectiveStatus}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.4 }}
            className="flex flex-col items-center gap-4"
          >
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              className="relative"
            >
              <div className="w-16 h-16 rounded-full bg-gradient-to-br from-[#1f4ed8] to-[#3b82f6] flex items-center justify-center text-white shadow-lg">
                {activeStage.icon}
              </div>
              <motion.div
                className="absolute inset-0 rounded-full border-4 border-[#1f4ed8] border-t-transparent"
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              />
            </motion.div>
            <div className="text-center">
              <h3 className="text-xl font-semibold text-[#0E0F14] mb-2">
                {activeStage.label}
              </h3>
              <p className="text-sm text-[#5A6066]">
                {activeStage.description}
              </p>
            </div>
          </motion.div>
        </AnimatePresence>

        {/* Progress Stages */}
        <div className="w-full space-y-4 relative">
          {STAGES.map((stage, index) => {
            const isCompleted = currentStageIndex > index;
            const isActive = currentStageIndex === index;

            return (
              <div key={stage.key} className="relative">
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="flex items-center gap-3 relative z-10"
                >
                  {/* Stage Indicator */}
                  <div className="flex-shrink-0 relative">
                    {isCompleted ? (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="w-8 h-8 rounded-full bg-[#10b981] flex items-center justify-center"
                      >
                        <CheckCircle2 className="w-5 h-5 text-white" />
                      </motion.div>
                    ) : isActive ? (
                      <motion.div
                        animate={{ scale: [1, 1.1, 1] }}
                        transition={{ duration: 1.5, repeat: Infinity }}
                        className="w-8 h-8 rounded-full bg-[#1f4ed8] flex items-center justify-center"
                      >
                        <Loader2 className="w-4 h-4 text-white animate-spin" />
                      </motion.div>
                    ) : (
                      <div className="w-8 h-8 rounded-full bg-[#e5e7eb] flex items-center justify-center">
                        <div className="w-3 h-3 rounded-full bg-[#9ca3af]" />
                      </div>
                    )}
                  </div>

                  {/* Stage Label */}
                  <div className="flex-1">
                    <div
                      className={`text-sm font-medium transition-colors ${
                        isActive
                          ? 'text-[#1f4ed8]'
                          : isCompleted
                          ? 'text-[#10b981]'
                          : 'text-[#9ca3af]'
                      }`}
                    >
                      {stage.label}
                    </div>
                    {isActive && (
                      <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="text-xs text-[#6b7280] mt-0.5"
                      >
                        {stage.description}
                      </motion.div>
                    )}
                  </div>
                </motion.div>

                {/* Progress Bar - Connector Line */}
                {index < STAGES.length - 1 && (
                  <div className="absolute left-4 top-8 w-0.5 h-6 bg-[#e5e7eb] -z-0">
                    {isCompleted && (
                      <motion.div
                        initial={{ height: 0 }}
                        animate={{ height: '100%' }}
                        transition={{ duration: 0.5 }}
                        className="w-full bg-[#10b981]"
                      />
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>

      </div>
    </div>
  );
}

