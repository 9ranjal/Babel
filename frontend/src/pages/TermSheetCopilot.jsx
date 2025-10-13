import React, { useCallback, useState } from "react";
import CopilotChat from "../components/CopilotChat";
import TermSheetEditor from "../components/TermSheetEditor";
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from "../components/ui/resizable";
import { Button } from "../components/ui/button";
import { Avatar, AvatarFallback } from "../components/ui/avatar";
import { CreditCard, HelpCircle, Sparkles } from "lucide-react";

export default function TermSheetCopilot() {
  const [incomingSuggestion, setIncomingSuggestion] = useState(null);

  const onSuggestion = useCallback((s) => {
    setIncomingSuggestion(s);
    setTimeout(() => setIncomingSuggestion(null), 0);
  }, []);

  return (
    <div className="h-screen w-screen bg-zinc-100 text-zinc-900" style={{ fontFamily: 'Inter, ui-sans-serif, system-ui' }}>
      {/* App Header */}
      <div className="h-12 border-b border-zinc-200 bg-white flex items-center justify-between px-4">
        <div className="flex items-center gap-2">
          <Sparkles size={16} className="text-indigo-600" />
          <div className="text-sm font-medium tracking-wide">Termcraft AI</div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" className="bg-zinc-100 hover:bg-zinc-200 text-zinc-800 h-8 px-3">
            <HelpCircle size={14} className="mr-1" /> Help
          </Button>
          <Button className="bg-indigo-600 hover:bg-indigo-700 h-8 px-3">
            <CreditCard size={14} className="mr-1" /> Buy Credits
          </Button>
          <Avatar className="h-8 w-8">
            <AvatarFallback className="bg-indigo-50 text-indigo-700 text-xs">TC</AvatarFallback>
          </Avatar>
        </div>
      </div>

      {/* Main Panels */}
      <ResizablePanelGroup direction="horizontal" className="h-[calc(100vh-48px)]">
        <ResizablePanel defaultSize={40} minSize={28} maxSize={55}>
          <CopilotChat onSuggestion={onSuggestion} />
        </ResizablePanel>
        <ResizableHandle withHandle />
        <ResizablePanel defaultSize={60} minSize={45}>
          <TermSheetEditor incomingSuggestion={incomingSuggestion} />
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
}
