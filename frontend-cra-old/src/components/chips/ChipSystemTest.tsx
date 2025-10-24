import React from 'react';
import { ChipCollection } from './index';

/**
 * Simple test component to verify chip system integration
 */
export const ChipSystemTest: React.FC = () => {
  const handleInformationUpdate = (state: any) => {
    console.log('Information updated:', state);
  };

  const handleTermSheetReady = (data: any) => {
    console.log('Term sheet ready:', data);
  };

  return (
    <div className="h-screen">
      <ChipCollection
        onInformationUpdate={handleInformationUpdate}
        onTermSheetReady={handleTermSheetReady}
      />
    </div>
  );
};

export default ChipSystemTest;
