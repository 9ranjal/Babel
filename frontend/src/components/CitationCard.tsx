import { motion } from 'framer-motion';

interface Citation {
  id: string | number;
  source_type: "note" | "quiz" | "flashcard" | "web";
  span?: { start: number; end: number };
  // Web citation fields
  title?: string;
  domain?: string;
  url?: string;
  icon?: string;
  snippet?: string;
}

interface CitationCardProps {
  citation: Citation;
  index: number;
  isPopup?: boolean;
  onClose?: () => void;
}

export default function CitationCard({ citation, index, isPopup = false, onClose }: CitationCardProps) {
  // Handle internal citations (note/quiz/flashcard)
  if (citation.source_type !== 'web') {
    return (
      <div className={`text-xs text-zinc-400 bg-zinc-800/50 rounded-lg p-2 border border-zinc-700/50 ${isPopup ? 'max-w-sm' : ''}`}>
        <span className="font-medium">{citation.source_type}:</span> {citation.id}
        {citation.span && (
          <span className="text-zinc-500 ml-1">
            (lines {citation.span.start}-{citation.span.end})
          </span>
        )}
      </div>
    );
  }

  // Handle web citations (Serper/web search)
  const { title, domain, url, icon, snippet } = citation;

  const getDomainColor = (domain: string) => {
    const d = domain.toLowerCase();
    if (d.includes('gov') || d.includes('pib')) return 'text-white bg-blue-600 border-blue-700';
    if (d.includes('edu') || d.includes('university')) return 'text-white bg-purple-600 border-purple-700';
    if (d.includes('times') || d.includes('hindu') || d.includes('express')) return 'text-white bg-orange-600 border-orange-700';
    return 'text-white bg-gray-600 border-gray-700 tracking-wide uppercase text-[10px]';
  };

  const content = (
    <div className={`group ${isPopup ? 'max-w-sm' : ''}`}>
      <div className="flex items-start gap-2">
        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Title and domain */}
          <div className="flex items-start justify-between gap-2 mb-1.5">
            <div className="flex-1 min-w-0">
              <div className="text-sm font-semibold text-black group-hover:text-gray-800 leading-tight mb-1">
                {title || `Source ${index + 1}`}
              </div>
              <div className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border ${getDomainColor(domain || '')}`}>
                <span className="truncate tracking-wide">{domain || 'web source'}</span>
              </div>
            </div>
          </div>

          {/* Compact Snippet */}
          {snippet && (
            <div className="text-xs text-black leading-relaxed line-clamp-2 mt-2">
              {snippet}
            </div>
          )}
        </div>
      </div>
    </div>
  );

  if (isPopup) {
    return (
      <div className="relative">
        <div className="border border-blue-200/60 dark:border-blue-700/60 rounded-xl p-4 shadow-2xl max-w-sm" style={{ backgroundColor: '#FFD700' }}>
          {/* Accent strip for popup */}
          <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-indigo-500 to-purple-500 rounded-l-xl"></div>
          {content}
          {onClose && (
            <button
              onClick={onClose}
              className="absolute top-3 right-3 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors text-lg font-bold w-6 h-6 flex items-center justify-center rounded-full hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              ×
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <motion.a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="group relative block border border-blue-200/60 dark:border-blue-700/60 rounded-xl p-4 transition-all duration-200 hover:shadow-lg"
      style={{ backgroundColor: '#FFD700' }}
      whileHover={{ scale: 1.01, y: -1 }}
      whileTap={{ scale: 0.99 }}
      transition={{ duration: 0.2, ease: [0.4, 0, 0.2, 1] }}
    >
      {/* Accent strip */}
      <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-indigo-500 to-purple-500 rounded-l-xl"></div>
      {content}
    </motion.a>
  );
}

