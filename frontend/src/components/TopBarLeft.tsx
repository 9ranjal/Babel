import React from 'react';

interface TopBarLeftProps {
  isLeftPanelCollapsed?: boolean;
  toggleLeftPanel?: () => void;
  activeModule?: string;
}

const TopBarLeft: React.FC<TopBarLeftProps> = ({
  isLeftPanelCollapsed = false,
  toggleLeftPanel = () => {},
  activeModule = ''
}) => {
  return (
    <div 
      className="flex items-center h-[40px] px-2 relative z-20 flex-1 justify-end"
    >
      <div className="w-full h-full flex items-center justify-end">
        {/* Right Section - Empty after removing Feedback and Login */}
      </div>
    </div>
  );
};

export default TopBarLeft;
