import { useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import axios from "axios";
import TermSheetCopilot from "./pages/TermSheetCopilot";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function AppRoot() {
  useEffect(() => {
    // Ping backend root just to verify connectivity (safe no-op)
    axios.get(`${API}/`).catch(() => {});
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
