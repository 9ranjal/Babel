import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from './ui/Button';
import { ArrowRight } from 'lucide-react';

export const LandingCTA: React.FC = () => {
  const navigate = useNavigate();
  const [hovered, setHovered] = useState<'left' | 'right' | null>(null);

  const baseStyles = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '16px 32px',
    fontSize: '18px',
    fontWeight: 600,
    color: '#0E0F14',
    backgroundColor: 'transparent',
    border: '2px solid #F0E68C',
    borderRadius: '12px',
    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    cursor: 'pointer',
    outline: 'none',
  };

  return (
    <div className="flex flex-col sm:flex-row gap-4 sm:gap-8 items-center justify-center">
      <button
        style={{
          ...baseStyles,
          marginRight: '8px',
          backgroundColor: hovered === 'left' ? '#F0E68C' : 'transparent',
          boxShadow: hovered === 'left' ? '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)' : '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
          transform: hovered === 'left' ? 'translateY(-3px) scale(1.05)' : 'translateY(0) scale(1)'
        }}
        onMouseEnter={() => setHovered('left')}
        onMouseLeave={() => setHovered(null)}
        onMouseDown={(e) => {
          e.currentTarget.style.transform = 'translateY(0) scale(0.98)';
        }}
        onClick={() => navigate('/chat')}
      >
        Babel
      </button>
      
      <button
        style={{
          ...baseStyles,
          marginLeft: '8px',
          backgroundColor: hovered === 'right' ? '#F0E68C' : 'transparent',
          boxShadow: hovered === 'right' ? '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)' : '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
          transform: hovered === 'right' ? 'translateY(-3px) scale(1.05)' : 'translateY(0) scale(1)'
        }}
        onMouseEnter={() => setHovered('right')}
        onMouseLeave={() => setHovered(null)}
        onMouseDown={(e) => {
          e.currentTarget.style.transform = 'translateY(0) scale(0.98)';
        }}
        onClick={() => navigate('/faq')}
      >
        FAQ
      </button>
    </div>
  );
};

