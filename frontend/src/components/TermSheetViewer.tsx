import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Download, FileText } from 'lucide-react';
import { Button } from './ui/Button';

interface TermSheetViewerProps {
  content?: string;
  title?: string;
}

export default function TermSheetViewer({ content, title = 'Term Sheet' }: TermSheetViewerProps) {
  const [termSheetContent, setTermSheetContent] = useState(content || '');

  useEffect(() => {
    if (content) {
      setTermSheetContent(content);
    }
  }, [content]);

  const downloadMarkdown = () => {
    const blob = new Blob([termSheetContent], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title.replace(/\s+/g, '_')}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="px-6 py-4 border-b border-zinc-200 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <FileText size={20} className="text-indigo-600" />
          <h2 className="text-lg font-semibold text-zinc-900">{title}</h2>
        </div>
        {termSheetContent && (
          <Button
            variant="outline"
            size="sm"
            onClick={downloadMarkdown}
          >
            <Download size={14} className="mr-2" />
            Download
          </Button>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {termSheetContent ? (
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown 
              remarkPlugins={[remarkGfm]}
              components={{
                table: ({ children }) => (
                  <div className="overflow-x-auto my-4">
                    <table className="min-w-full border border-zinc-300">{children}</table>
                  </div>
                ),
                th: ({ children }) => (
                  <th className="border border-zinc-300 bg-zinc-50 px-4 py-2 text-left font-semibold">
                    {children}
                  </th>
                ),
                td: ({ children }) => (
                  <td className="border border-zinc-300 px-4 py-2">{children}</td>
                ),
                h1: ({ children }) => <h1 className="text-2xl font-bold mb-4 text-zinc-900">{children}</h1>,
                h2: ({ children }) => <h2 className="text-xl font-semibold mt-6 mb-3 text-zinc-900">{children}</h2>,
                h3: ({ children }) => <h3 className="text-lg font-medium mt-4 mb-2 text-zinc-900">{children}</h3>,
                p: ({ children }) => <p className="mb-3 text-zinc-700 leading-relaxed">{children}</p>,
                ul: ({ children }) => <ul className="list-disc pl-6 mb-4 space-y-2">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal pl-6 mb-4 space-y-2">{children}</ol>,
                li: ({ children }) => <li className="text-zinc-700">{children}</li>,
                code: ({ children }) => (
                  <code className="bg-zinc-100 rounded px-1.5 py-0.5 text-sm font-mono">{children}</code>
                ),
              }}
            >
              {termSheetContent}
            </ReactMarkdown>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-center text-zinc-500">
            <FileText size={48} className="mb-4 text-zinc-300" />
            <h3 className="text-lg font-medium text-zinc-700 mb-2">No Term Sheet Yet</h3>
            <p className="text-sm max-w-md">
              Start a conversation with the copilot to generate a term sheet, or ask it to explain specific clauses.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

