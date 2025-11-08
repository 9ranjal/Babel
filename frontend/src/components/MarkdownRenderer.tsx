import React, { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface Citation {
  id: string | number;
  source_type: "note" | "quiz" | "flashcard" | "web";
  title?: string;
  domain?: string;
  url?: string;
  snippet?: string;
}

interface MarkdownRendererProps {
  content: string;
  withCodeCopy?: boolean;
  className?: string;
  citations?: Citation[];
  onLinkClick?: (href: string) => boolean;
  onPIBArticleClick?: (cmd: string) => void;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({
  content,
  withCodeCopy = true,
  className,
  citations = [],
  onLinkClick,
  onPIBArticleClick,
}) => {
  const safeCitations = Array.isArray(citations) ? citations : [];

  const onCopy = async (text: string) => {
    try { 
      await navigator.clipboard.writeText(text); 
    } catch {}
  };

  return (
    <div className={className || 'prose prose-invert max-w-none prose-headings:scroll-mt-24'}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          img: ({ src, alt }) => (
            <img
              src={typeof src === 'string' ? src : ''}
              alt={typeof alt === 'string' ? alt : ''}
              loading="lazy"
              decoding="async"
              className="max-w-full h-auto rounded-md"
            />
          ),
          p: ({ children, ...props }) => {
            const childArray = React.Children.toArray(children);

            const renderTextWithCitations = (text: string, baseKey: string) => {
              const parts = text.split(/(\[[S]?\d+(?:\]\[[S]?\d+)*\])/g);
              return parts.map((part, index) => {
                const citationMatch = part.match(/^\[([S]?\d+(?:\]\[[S]?\d+)*)\]$/);
                if (citationMatch) {
                  const citationNumbers = part.match(/[S]?(\d+)/g) || [];
                  return citationNumbers.map((num, idx) => {
                    const citationIndex = parseInt(num.replace('S', ''), 10) - 1;
                    const citation = safeCitations[citationIndex];
                    if (citation) {
                      const siteName = citation.domain ? citation.domain.replace('www.', '').split('.')[0] : `Source ${num}`;
                      return (
                        <span
                          key={`${baseKey}-${index}-${idx}-${citationIndex}`}
                          className="citation-pill-v2"
                          style={{
                            backgroundColor: '#F0E68C',
                            color: '#1f2937',
                            padding: '0.375rem 1rem',
                            borderRadius: '9999px',
                            fontSize: '0.75rem',
                            fontWeight: '500',
                            cursor: 'pointer',
                            display: 'inline-block',
                            transition: 'all 0.2s ease',
                            marginLeft: '0.25rem',
                            marginRight: '0.25rem',
                          }}
                        >
                          {siteName}
                        </span>
                      );
                    }
                    return (
                      <span key={`${baseKey}-${index}-${idx}`} className="text-gray-600">
                        [{num}]
                      </span>
                    );
                  });
                }
                return part;
              });
            };

            const hasBlockChild = childArray.some((child) => {
              if (!React.isValidElement(child)) return false;
              const blockTags = ['pre', 'div', 'table', 'ul', 'ol', 'blockquote', 'code'];
              const tag = typeof child.type === 'string' ? child.type : undefined;
              return tag ? blockTags.includes(tag) : false;
            });

            const renderedChildren = childArray.map((child, index) => {
              if (typeof child === 'string') {
                return (
                  <React.Fragment key={`text-${index}`}>
                    {renderTextWithCitations(child, `text-${index}`)}
                  </React.Fragment>
                );
              }
              return child;
            });

            const Wrapper = hasBlockChild ? 'div' : 'p';

            return (
              <Wrapper className="mb-3 leading-relaxed text-[#2b2c28]" {...props}>
                {renderedChildren}
              </Wrapper>
            );
          },
          h1: ({ children }) => (
            <h1 className="text-2xl font-bold mb-4 text-[#2b2c28]">{children}</h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-xl font-semibold mb-3 text-[#0f766e]">{children}</h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-lg font-medium mb-2 text-[#2b2c28]">{children}</h3>
          ),
          ul: ({ children }) => (
            <ul className="mb-4 ml-6 list-disc space-y-1 text-[#2b2c28]">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="mb-4 ml-6 list-decimal space-y-1 text-[#2b2c28]">{children}</ol>
          ),
          li: ({ children, ...props }) => (
            <li className="text-[#2b2c28] leading-relaxed" {...props}>{children}</li>
          ),
          hr: () => <hr className="my-6 border-zinc-600" />,
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-zinc-600 pl-4 my-4 italic text-[#2b2c28]">
              {children}
            </blockquote>
          ),
          a: ({ children, href, ...props }) => {
            const handleAnchorClick = (event: React.MouseEvent<HTMLAnchorElement>) => {
              if (href && onLinkClick) {
                const intercepted = onLinkClick(href);
                if (intercepted) {
                  event.preventDefault();
                }
              }
            };
            return (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="underline decoration-zinc-500 hover:decoration-zinc-300"
                onClick={handleAnchorClick}
                {...props}
              >
                {children}
              </a>
            );
          },
          code: ({ inline, className, children, ...props }: any) => {
            const codeText = String(children);
            if (inline) {
              return (
                <code className="bg-zinc-800/70 px-1 py-0.5 rounded text-sm" {...props}>
                  {children}
                </code>
              );
            }
            if (!withCodeCopy) {
              return (
                <pre className="bg-zinc-900 p-3 rounded overflow-auto">
                  <code className={className} {...props}>{children}</code>
                </pre>
              );
            }
            return (
              <div className="relative group mb-3">
                <button
                  onClick={() => onCopy(codeText)}
                  className="absolute top-2 right-2 text-xs px-2 py-1 rounded bg-zinc-700 text-zinc-300 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  Copy
                </button>
                <pre className="bg-zinc-900 p-3 rounded overflow-auto">
                  <code className={className} {...props}>{children}</code>
                </pre>
              </div>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default MarkdownRenderer;

