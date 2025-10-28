import React, { ReactNode } from 'react';

type MarketingLayoutProps = {
  children: ReactNode;
};

export const MarketingLayout: React.FC<MarketingLayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-[#F6F1EA] relative">
      {children}
    </div>
  );
};
