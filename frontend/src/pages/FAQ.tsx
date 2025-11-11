import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';

export const FAQsPage: React.FC = () => {
  const navigate = useNavigate();
  const [hovered, setHovered] = useState(false);
  // Simple function to parse markdown-style formatting and bullets/newlines
  const parseMarkdown = (text: string) => {
    // Bold and italic (must process bold-italic first)
    let html = text
      .replace(/\*\*\*(.*?)\*\*\*/g, '<strong><em>$1</em></strong>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Convert leading bullet lines (• ) into a proper list
    const rawLines = html.split('\n');
    const bulletLines = rawLines.filter((l) => l.trim().startsWith('•'));
    if (bulletLines.length > 0) {
      const items = rawLines
        .filter((l) => l.trim().length > 0)
        .map((l) => {
          const trimmed = l.trim();
          if (trimmed.startsWith('•')) {
            return `<li>${trimmed.replace(/^•\s?/, '')}</li>`;
          }
          return `<li>${trimmed}</li>`;
        })
        .join('');
      return `<ul class="list-disc space-y-3" style="padding-left: 1.5rem; margin: 0;">${items}</ul>`;
    }

    // Fallback: convert newlines to <br/>
    return html.replace(/\n/g, '<br/>');
  };

  const faqs = [
    {
      question: 'What is Babel?',
      answer:
        "**Babel** is the ***consensus layer for venture capital***. It brings founders and investors onto a shared platform to align faster and close deals seamlessly.\n\nWe're building the infrastructure for trust in **VC negotiations** through **Consensus as a Service (CaaS)**.",
    },
    {
      question: 'What is Consensus as a Service (CaaS)?',
      answer:
        "**CaaS** is our mathematically-grounded negotiation engine that blends ***leverage-based modeling*** with AI reasoning.\n\nUnlike prompt-wrapped LLMs that ***hallucinate under pressure***, our **ZOPA engine** runs ***simulated negotiations***, computes **leverage scores**, and feeds those signals into the model—anchoring every recommendation in math, not guesswork.",
    },
    {
      question: "Why we're different",
      answer:
        "Most legaltech tools ***isolate parties and hide logic***. We connect **both sides on one transparent interface**, showing every **leverage score** and ***negotiation path***.\n\nBy pairing ***deterministic math with AI consensus-building***, we're redefining how **venture capital finds common ground**.",
    },
  ];

  return (
    <div className="min-h-screen bg-[#F6F1EA] py-12" style={{ paddingLeft: '19.6875vw', paddingRight: '19.6875vw' }}>
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <h1 className="text-4xl md:text-5xl font-bold text-[#0E0F14] mb-4">Frequently Asked Questions</h1>
          <p className="text-xl text-[#0E0F14] opacity-70 max-w-2xl mx-auto">
            Discover how our mathematically-grounded approach transforms negotiations from adversarial battles into collaborative consensus-building.
          </p>
        </motion.div>

        {/* FAQ Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="space-y-8 mb-16"
        >
          {faqs.map((faq, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.3 + index * 0.1 }}
              className="border"
              style={{ 
                backgroundColor: 'rgba(240, 230, 140, 0.20)',
                borderColor: 'rgba(240, 230, 140, 0.40)',
                borderRadius: '1.5rem',
                backdropFilter: 'blur(4px)',
                WebkitBackdropFilter: 'blur(4px)',
                boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
                padding: '0.91rem',
                marginBottom: index < faqs.length - 1 ? '2rem' : '0'
              }}
            >
              <h3 className="text-xl font-semibold text-[#0E0F14] mb-3">{faq.question}</h3>
              <p
                className="text-base text-[#0E0F14] opacity-80 leading-relaxed mb-4"
                dangerouslySetInnerHTML={{ __html: parseMarkdown(faq.answer) }}
              />
            </motion.div>
          ))}
        </motion.div>

        {/* CTA Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.8 }}
          style={{ marginTop: '3rem', paddingBottom: '3rem' }}
        >
          <div style={{ display: 'flex', justifyContent: 'center' }}>
            <button
              onClick={() => navigate('/')}
              onMouseEnter={() => setHovered(true)}
              onMouseLeave={() => setHovered(false)}
              onMouseDown={(e) => {
                e.currentTarget.style.transform = 'translateY(0) scale(0.98)';
              }}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '16px 32px',
                fontSize: '18px',
                fontWeight: 600,
                color: '#0E0F14',
                backgroundColor: hovered ? '#F0E68C' : 'transparent',
                border: '2px solid #F0E68C',
                borderRadius: '12px',
                boxShadow: hovered ? '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)' : '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                cursor: 'pointer',
                outline: 'none',
                transform: hovered ? 'translateY(-3px) scale(1.05)' : 'translateY(0) scale(1)'
              }}
            >
              Get Started
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

// Keep compatibility with existing imports
export { FAQsPage as FAQ };
