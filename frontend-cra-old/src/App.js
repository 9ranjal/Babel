import { useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import axios from "axios";
import TermSheetCopilot from "./pages/TermSheetCopilot";
import TermCraftApp from "./pages/TermCraftApp.tsx";
import SimpleChat from "./pages/SimpleChat.tsx";

const BACKEND_URL = process.env.REACT_APP_API_BASE || 'http://localhost:5002';
const API = `${BACKEND_URL}/api`;

function AppRoot() {
  useEffect(() => {
    // Ping backend root just to verify connectivity (safe no-op)
    axios.get(`${BACKEND_URL}/`).catch(() => {});
  }, []);

  return <TermSheetCopilot />;
}

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppRoot />} />
          <Route path="/transaction" element={<TermCraftApp />} />
          <Route path="/chat" element={<SimpleChat />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
