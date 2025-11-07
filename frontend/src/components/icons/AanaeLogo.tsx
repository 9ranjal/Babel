import React from 'react';

// Simple placeholder logo component
export default function AanaeLogo(props: React.SVGProps<SVGSVGElement>) {
  const { className = '', style, width = 24, height = 24, ...rest } = props;
  return (
    <svg
      className={className}
      width={width}
      height={height}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      style={{ display: 'block', background: 'transparent', ...(style || {}) }}
      {...rest}
    >
      <circle cx="12" cy="12" r="10" fill="currentColor" opacity="0.2" />
      <path d="M12 6v12M6 12h12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

