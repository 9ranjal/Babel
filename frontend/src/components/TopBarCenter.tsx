import React from 'react';

const TopBarCenter: React.FC = () => {
  return (
    <div className="flex-1 flex items-center justify-center h-[40px] md:h-[40px] relative">
      <div className="flex items-center gap-2">
        {/* Navigation modules can be added here if needed */}
      </div>
    </div>
  );
};

export default TopBarCenter;

