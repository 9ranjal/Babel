import React, { useCallback, useEffect, useMemo } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import { TableKit } from '@tiptap/extension-table';
import { marked } from 'marked';
import { gfmHeadingId } from 'marked-gfm-heading-id';
import { markedHighlight } from 'marked-highlight';
import { 
  Bold, 
  Italic, 
  List, 
  Table as TableIcon,
  Save,
  Undo,
  Redo
} from 'lucide-react';
import { Button } from './ui/Button';

interface TermSheetEditorProps {
  content: string; // Can be markdown or HTML
  onChange?: (content: string) => void;
  editable?: boolean;
}

export const TermSheetEditor: React.FC<TermSheetEditorProps> = ({
  content,
  onChange,
  editable = true,
}) => {
  // Convert markdown to HTML if needed, or use HTML directly
  const htmlContent = useMemo(() => {
    if (!content) return '';
    // Check if content is already HTML (contains HTML tags)
    if (content.trim().startsWith('<') || content.includes('<table') || content.includes('<p>') || content.includes('<h1>') || content.includes('<h2>')) {
      // Already HTML, use as-is
      return content;
    }
    // Otherwise, treat as markdown and convert
    try {
      // Configure marked to properly handle tables
      marked.setOptions({
        breaks: true,
        gfm: true,
        headerIds: false,
        mangle: false,
      });
      const html = marked.parse(content);
      return html;
    } catch (e) {
      console.error('Error converting markdown to HTML:', e);
      return content;
    }
  }, [content]);

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: {
          levels: [1, 2, 3],
        },
      }),
      TableKit.configure({
        resizable: true,
        HTMLAttributes: {
          class: 'term-sheet-table',
        },
      }),
    ],
    content: htmlContent,
    editable,
    onUpdate: ({ editor }) => {
      if (onChange) {
        onChange(editor.getHTML());
      }
    },
  });

  useEffect(() => {
    if (editor && htmlContent !== editor.getHTML()) {
      editor.commands.setContent(htmlContent);
    }
  }, [htmlContent, editor]);

  const addTable = useCallback(() => {
    if (editor) {
      editor.chain().focus().insertTable({ rows: 3, cols: 2, withHeaderRow: true }).run();
    }
  }, [editor]);

  const toggleBold = useCallback(() => {
    if (editor) {
      editor.chain().focus().toggleBold().run();
    }
  }, [editor]);

  const toggleItalic = useCallback(() => {
    if (editor) {
      editor.chain().focus().toggleItalic().run();
    }
  }, [editor]);

  const toggleBulletList = useCallback(() => {
    if (editor) {
      editor.chain().focus().toggleBulletList().run();
    }
  }, [editor]);

  const undo = useCallback(() => {
    if (editor) {
      editor.chain().focus().undo().run();
    }
  }, [editor]);

  const redo = useCallback(() => {
    if (editor) {
      editor.chain().focus().redo().run();
    }
  }, [editor]);

  if (!editor) {
    return <div className="p-4">Loading editor...</div>;
  }

  return (
    <div className="term-sheet-editor border border-gray-300 rounded-lg bg-white">
      {editable && (
        <div className="flex items-center gap-2 p-3 border-b border-gray-200 bg-gray-50 flex-wrap">
          <Button
            variant="outline"
            size="sm"
            onClick={toggleBold}
            className={editor.isActive('bold') ? 'bg-gray-200' : ''}
            title="Bold"
          >
            <Bold className="w-4 h-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={toggleItalic}
            className={editor.isActive('italic') ? 'bg-gray-200' : ''}
            title="Italic"
          >
            <Italic className="w-4 h-4" />
          </Button>
          <div className="w-px h-6 bg-gray-300 mx-1" />
          <Button
            variant="outline"
            size="sm"
            onClick={toggleBulletList}
            className={editor.isActive('bulletList') ? 'bg-gray-200' : ''}
            title="Bullet List"
          >
            <List className="w-4 h-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={addTable}
            title="Insert Table"
          >
            <TableIcon className="w-4 h-4" />
          </Button>
          <div className="w-px h-6 bg-gray-300 mx-1" />
          <Button
            variant="outline"
            size="sm"
            onClick={undo}
            disabled={!editor.can().undo()}
            title="Undo"
          >
            <Undo className="w-4 h-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={redo}
            disabled={!editor.can().redo()}
            title="Redo"
          >
            <Redo className="w-4 h-4" />
          </Button>
        </div>
      )}
      <div className="p-6 min-h-[400px] prose prose-sm max-w-none">
        <style>{`
          .term-sheet-editor .ProseMirror {
            outline: none;
            min-height: 400px;
          }
          .term-sheet-editor .ts-table {
            border-collapse: collapse;
            margin: 1rem 0;
            table-layout: fixed;
            width: 100%;
            border: 1px solid rgba(156, 163, 175, 0.3);
            background: white;
            font-size: 14px;
            line-height: 1.5;
          }
          .term-sheet-editor .ts-table th,
          .term-sheet-editor .ts-table td {
            padding: 6px 8px;
            border: 1px solid rgba(156, 163, 175, 0.3);
            vertical-align: top;
            text-align: left;
          }
          .term-sheet-editor .ts-table th {
            background: #f9fafb;
            font-weight: 600;
            text-transform: none;
            color: #1f2937;
            width: 35%;
            min-width: 150px;
          }
          .term-sheet-editor .ts-table td {
            width: 65%;
            color: #374151;
          }
          .term-sheet-editor .ts-table tr:nth-child(odd) td {
            background: rgba(249, 250, 251, 0.5);
          }
          .term-sheet-editor .ts-table tr:nth-child(even) td {
            background: white;
          }
          .term-sheet-editor .ts-table tr:nth-child(odd) th {
            background: #f9fafb;
          }
          .term-sheet-editor .ts-table tr:nth-child(even) th {
            background: #f9fafb;
          }
          .term-sheet-editor .ts-table td[colspan="2"] {
            width: 100%;
            padding: 8px 12px;
            font-size: 13px;
            line-height: 1.6;
            color: #4b5563;
          }
          .term-sheet-editor .term-sheet-table .selectedCell:after {
            z-index: 2;
            position: absolute;
            content: "";
            left: 0; right: 0; top: 0; bottom: 0;
            background: rgba(200, 200, 255, 0.4);
            pointer-events: none;
          }
          .term-sheet-editor .term-sheet-table .column-resize-handle {
            position: absolute;
            right: -2px;
            top: 0;
            bottom: -2px;
            width: 4px;
            background-color: #3b82f6;
            pointer-events: none;
          }
          .term-sheet-editor .ProseMirror p {
            margin: 0.5rem 0;
          }
          .term-sheet-editor .ProseMirror h1 {
            font-size: 1.875rem;
            font-weight: 700;
            margin: 1rem 0;
          }
          .term-sheet-editor .ProseMirror h2 {
            font-size: 1.5rem;
            font-weight: 600;
            margin: 0.75rem 0;
          }
          .term-sheet-editor .ProseMirror h3 {
            font-size: 1.25rem;
            font-weight: 600;
            margin: 0.5rem 0;
          }
          .term-sheet-editor .ProseMirror ul,
          .term-sheet-editor .ProseMirror ol {
            margin: 0.5rem 0;
            padding-left: 1.5rem;
          }
          .term-sheet-editor .ProseMirror strong {
            font-weight: 600;
          }
          .term-sheet-editor .ProseMirror em {
            font-style: italic;
          }
        `}</style>
        <EditorContent editor={editor} />
      </div>
    </div>
  );
};

