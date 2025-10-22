import { useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { api } from "./lib/apiClient";
import TermSheetCopilot from "./pages/TermSheetCopilot";

function AppRoot() {
  useEffect(() => {
    // Ping backend root just to verify connectivity (safe no-op)
    api.get("/").catch(() => {});
  }, []);

  return <TermSheetCopilot />;
}

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppRoot />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
