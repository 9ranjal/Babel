import React, { useEffect, useMemo, useRef, useState } from "react";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { Popover, PopoverContent, PopoverTrigger } from "../components/ui/popover";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "../components/ui/tooltip";
import { ScrollArea } from "../components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Separator } from "../components/ui/separator";
import { Download, History, Check, X, MessageSquarePlus, StickyNote } from "lucide-react";
import { loadInitialState, persistState } from "../mock";

function applySuggestion(text, suggestion) {
  if (!suggestion) return text;
  if (suggestion.type === "replace") {
    return text.replace(suggestion.pattern, suggestion.replaceWith);
  }
  return text;
}

function removeSuggestion(text, suggestion) {
  // For replace, just keep original text (no-op as we didn't change state yet for preview-only)
  return text;
}

export default function TermSheetEditor({ incomingSuggestion }) {
  const init = loadInitialState();
  const [title, setTitle] = useState("Seed Preferred Financing — Draft #1");
  const [text, setText] = useState(init.text);
  const [versions, setVersions] = useState(init.versions);
  const [comments, setComments] = useState(init.comments);
  const [pending, setPending] = useState([]); // array of suggestions
  const [tab, setTab] = useState("editor");

  useEffect(() => {
    persistState({ text, versions, comments });
  }, [text, versions, comments]);

  useEffect(() => {
    if (incomingSuggestion) {
      setPending((p) => [incomingSuggestion, ...p]);
      setTab("editor");
    }
  }, [incomingSuggestion]);

  const acceptSuggestion = (sugg) => {
    const newText = applySuggestion(text, sugg);
    setText(newText);
    setPending((p) => p.filter((s) => s.id !== sugg.id));
    saveVersion("Accepted: " + (sugg.clauseHint || sugg.pattern));
  };

  const rejectSuggestion = (sugg) => {
    setPending((p) => p.filter((s) => s.id !== sugg.id));
  };

  const acceptAll = () => {
    let t = text;
    pending.forEach((s) => {
      t = applySuggestion(t, s);
    });
    setText(t);
    setPending([]);
    saveVersion("Accepted all suggestions");
  };

  const rejectAll = () => setPending([]);

  const saveVersion = (note = "Manual save") => {
    const v = {
      id: `v-${Date.now()}`,
      title,
      note,
      text,
      ts: Date.now(),
    };
    const next = [v, ...versions].slice(0, 20);
    setVersions(next);
  };

  const restoreVersion = (v) => {
    setTitle(v.title + " (restored)");
    setText(v.text);
  };

  const addCommentAtSelection = (note) => {
    const selection = window.getSelection();
    const snippet = selection?.toString() || "";
    if (!snippet) return;
    const newC = {
      id: `c-${Date.now()}`,
      snippet: snippet.slice(0, 80),
      note,
      anchorPattern: snippet.slice(0, 80),
      ts: Date.now(),
    };
    setComments([newC, ...comments]);
  };

  const exportMarkdown = () => {
    const blob = new Blob([`# ${title}\n\n` + text], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${title.replace(/[^a-z0-9\-]/gi, "_")}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const highlightedText = useMemo(() => {
    // Render pending suggestions as simple inline redlines before acceptance
    let html = text;
    pending.forEach((s) => {
      if (s.type === "replace") {
        const pattern = s.pattern.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
        const reg = new RegExp(pattern, "g");
        html = html.replace(
          reg,
          (m) =>
            `<span class='line-through text-red-600/90 bg-red-50 rounded px-1'>${m}</span> ` +
            `<span class='bg-green-50 text-green-800 border border-green-200 rounded px-1'>${s.replaceWith}</span>`
        );
      }
    });
    // Comments: underline anchors
    comments.forEach((c) => {
      const pattern = c.anchorPattern.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      const reg = new RegExp(pattern, "g");
      html = html.replace(
        reg,
        (m) => `<span class='underline decoration-indigo-400 decoration-2 underline-offset-4 cursor-help' data-comment='${c.id}'>${m}</span>`
      );
    });
    return html;
  }, [text, pending, comments]);

  return (
    <div className="h-full flex flex-col">
      <div className="px-4 py-3 flex items-center justify-between border-b border-zinc-200 bg-white/70 backdrop-blur">
        <div className="flex items-center gap-3">
          <Input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="font-medium text-zinc-900"
          />
          <Badge className="bg-zinc-100 text-zinc-700">Draft</Badge>
        </div>
        <div className="flex items-center gap-2">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="secondary" className="bg-zinc-100 hover:bg-zinc-200 text-zinc-800" onClick={exportMarkdown}>
                  <Download size={16} className="mr-2" /> Export
                </Button>
              </TooltipTrigger>
              <TooltipContent className="text-xs">Export current draft to Markdown (.md)</TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <Button variant="secondary" className="bg-zinc-100 hover:bg-zinc-200 text-zinc-800" onClick={() => saveVersion("Manual save") }>
            <History size={16} className="mr-2" /> Save Version
          </Button>

          <Button className="bg-emerald-600 hover:bg-emerald-700" onClick={acceptAll}>
            <Check size={16} className="mr-2" /> Accept All
          </Button>
          <Button variant="destructive" onClick={rejectAll}>
            <X size={16} className="mr-2" /> Reject All
          </Button>
        </div>
      </div>

      <Tabs value={tab} onValueChange={setTab} className="flex-1 flex flex-col">
        <TabsList className="px-2">
          <TabsTrigger value="editor">Editor</TabsTrigger>
          <TabsTrigger value="versions">Version History</TabsTrigger>
          <TabsTrigger value="comments">Comments</TabsTrigger>
        </TabsList>

        <TabsContent value="editor" className="flex-1 overflow-hidden">
          <div className="grid grid-cols-12 h-full">
            <div className="col-span-9 h-full border-r border-zinc-200">
              <div className="h-full p-6">
                <div className="prose max-w-none font-serif text-[15.5px] leading-7 text-zinc-900" style={{ fontFamily: '"Source Serif 4", ui-serif, Georgia, Cambria, Times, serif' }}>
                  <div className="mb-3 text-xs text-zinc-500">Click anywhere to edit. Select text and use the + bubble to comment.</div>
                  <div
                    contentEditable
                    suppressContentEditableWarning
                    className="outline-none min-h-[520px] whitespace-pre-wrap"
                    onInput={(e) => setText(e.currentTarget.textContent)}
                    dangerouslySetInnerHTML={{ __html: highlightedText }}
                  />
                </div>
              </div>
            </div>
            <div className="col-span-3 h-full bg-zinc-50/80">
              <div className="p-4">
                <div className="text-xs uppercase tracking-wide text-zinc-500 mb-2">Pending Suggestions</div>
                <div className="space-y-2">
                  {pending.length === 0 ? (
                    <div className="text-xs text-zinc-500">No pending suggestions</div>
                  ) : (
                    pending.map((s) => (
                      <div key={s.id} className="border border-zinc-200 bg-white rounded p-3 text-sm">
                        <div className="font-medium text-zinc-900">{s.clauseHint || s.pattern}</div>
                        <div className="text-zinc-700 mt-1">{s.rationale || "Suggested edit"}</div>
                        <div className="mt-2 flex gap-2">
                          <Button size="sm" className="h-7 px-2 bg-emerald-600 hover:bg-emerald-700" onClick={() => acceptSuggestion(s)}>
                            <Check size={14} className="mr-1" /> Accept
                          </Button>
                          <Button size="sm" variant="destructive" className="h-7 px-2" onClick={() => rejectSuggestion(s)}>
                            <X size={14} className="mr-1" /> Reject
                          </Button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="versions" className="flex-1 overflow-auto">
          <div className="p-4 space-y-3">
            {versions.length === 0 ? (
              <div className="text-sm text-zinc-500 p-4">No versions yet. Use “Save Version” or accept suggestions to create snapshots.</div>
            ) : (
              versions.map((v) => (
                <div key={v.id} className="border border-zinc-200 rounded bg-white p-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium text-zinc-900">{new Date(v.ts).toLocaleString()}</div>
                      <div className="text-xs text-zinc-500">{v.note}</div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button size="sm" variant="secondary" className="bg-zinc-100 hover:bg-zinc-200 text-zinc-800" onClick={() => restoreVersion(v)}>Restore</Button>
                    </div>
                  </div>
                  <Separator className="my-3" />
                  <div className="text-xs text-zinc-600 whitespace-pre-wrap max-h-40 overflow-auto">{v.text}</div>
                </div>
              ))
            )}
          </div>
        </TabsContent>

        <TabsContent value="comments" className="flex-1 overflow-auto">
          <div className="p-4 space-y-3">
            <AddCommentBox onAdd={addCommentAtSelection} />
            {comments.length === 0 ? (
              <div className="text-sm text-zinc-500 p-4">No comments yet.</div>
            ) : (
              comments.map((c) => (
                <div key={c.id} className="border border-zinc-200 rounded bg-white p-3">
                  <div className="text-xs text-zinc-500">{new Date(c.ts).toLocaleString()}</div>
                  <div className="font-medium text-zinc-900 mt-1">{c.snippet}</div>
                  <div className="text-sm text-zinc-700 mt-1">{c.note}</div>
                </div>
              ))
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function AddCommentBox({ onAdd }) {
  const [open, setOpen] = useState(false);
  const [note, setNote] = useState("");

  return (
    <div className="border border-dashed border-zinc-300 rounded p-3 bg-white/40">
      <div className="text-sm text-zinc-700 mb-2">Select text in the editor, then add a comment:</div>
      <div className="flex gap-2">
        <Textarea value={note} onChange={(e) => setNote(e.target.value)} placeholder="Write a comment about the selected clause…" />
        <Button
          className="bg-indigo-600 hover:bg-indigo-700"
          onClick={() => {
            if (!note.trim()) return;
            onAdd(note.trim());
            setNote("");
            setOpen(false);
          }}
        >
          <MessageSquarePlus size={16} className="mr-2" /> Add
        </Button>
      </div>
    </div>
  );
}
