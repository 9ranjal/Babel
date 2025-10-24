import React from 'react';
import ChipSystemDemo from '../components/chips/ChipSystemDemo';

/**
 * Chip-Based Information Collection Page
 * 
 * This page demonstrates the new chip-based information collection system
 * that replaces both the structured form and conversational intake approaches.
 * 
 * Features:
 * - Interactive chip-based information collection
 * - Progressive disclosure based on dependencies
 * - Real-time term sheet generation
 * - Contextual suggestions
 * - Industry-specific terms
 */

const ChipBasedIntake: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <ChipSystemDemo />
    </div>
  );
};

export default ChipBasedIntake;
