import React, { useCallback, useState } from "react";
import CopilotChat from "../components/CopilotChat";
import TermSheetEditor from "../components/TermSheetEditor";
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from "../components/ui/resizable";

export default function TermSheetCopilot() {
  const [incomingSuggestion, setIncomingSuggestion] = useState(null);

  const onSuggestion = useCallback((s) => {
    setIncomingSuggestion(s);
    // clear after delivering so subsequent updates are handled properly
    setTimeout(() => setIncomingSuggestion(null), 0);
  }, []);

  return (
    <div className="h-screen w-screen bg-zinc-100">
      <div className="h-12 border-b border-zinc-200 bg-white flex items-center px-4">
        <div className="text-sm text-zinc-600">Term Sheet Copilot</div>
      </div>
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
