// Placeholder API utilities for future integration. Do not hardcode URLs.
// Always use process.env.REACT_APP_BACKEND_URL and prefix all routes with '/api'.
import axios from "axios";

const BASE = process.env.REACT_APP_BACKEND_URL;
const API = `${BASE}/api`;

export async function suggestEdits({ sessionId, documentId, prompt, textSnapshot }) {
  // TODO: Wire to POST `${API}/suggest`
  // return axios.post(`${API}/suggest`, { sessionId, documentId, prompt, textSnapshot });
  return Promise.reject(new Error("Not implemented: Using mockAIResponse on frontend"));
}

export async function saveVersion({ documentId, title, text, note }) {
  // TODO: Wire to POST `${API}/versions`
  return Promise.reject(new Error("Not implemented: Local version persistence only (localStorage)"));
}

export async function addComment({ documentId, selection, note }) {
  // TODO: Wire to POST `${API}/comments`
  return Promise.reject(new Error("Not implemented: Local comments only (localStorage)"));
}

export function getApiBase() {
  return API;
}
