# Termcraft AI – API Contracts and Integration Plan

Status: Frontend-only MVP with mocked AI and localStorage persistence. This document defines the backend contracts and integration plan to plug FastAPI + MongoDB + GPT-4 + Yjs.

## Data Models
(All documents stored in MongoDB; snake_case keys over the wire; ISO timestamps.)

- Session
  - id: string (uuid)
  - created_at: datetime
  - client_meta: object (ua, ip, etc.)

- Document
  - id: string (uuid)
  - title: string
  - text_md: string (markdown/plaintext)
  - created_at: datetime
  - updated_at: datetime

- Version
  - id: string (uuid)
  - document_id: string
  - title: string
  - note: string
  - text_md: string
  - created_at: datetime

- Comment
  - id: string (uuid)
  - document_id: string
  - anchor:
    - type: "text" | "range" | "pos"
    - text?: string (anchor text snapshot)
    - start?: number (offset in text_md)
    - end?: number
  - note: string
  - created_at: datetime

- Suggestion
  - id: string (uuid)
  - document_id: string
  - type: "insert" | "delete" | "replace"
  - range: { start: number, end: number }  // byte or codepoint offset in text_md
  - before_text?: string  // for context/validation
  - after_text?: string
  - rationale?: string
  - clause_hint?: string
  - created_at: datetime
  - status: "pending" | "accepted" | "rejected"

- Message (chat)
  - id: string (uuid)
  - session_id: string
  - role: "user" | "assistant"
  - content: string
  - suggestions?: Suggestion[]  // optional suggestions attached to assistant reply
  - created_at: datetime

## API Contracts (all routes prefixed with /api)
Base: ${REACT_APP_BACKEND_URL}/api

- POST /sessions
  - body: { client_meta?: object }
  - 200: { id, created_at }

- GET /documents/:id
  - 200: Document

- POST /documents
  - body: { title: string, text_md: string }
  - 201: Document

- PATCH /documents/:id
  - body: { title?: string, text_md?: string }
  - 200: Document

- GET /versions?document_id=:id
  - 200: Version[] (desc created_at)

- POST /versions
  - body: { document_id, title, note, text_md }
  - 201: Version

- GET /comments?document_id=:id
  - 200: Comment[]

- POST /comments
  - body: { document_id, anchor, note }
  - 201: Comment

- DELETE /comments/:id
  - 204

- POST /suggest
  - body: { session_id, document_id, prompt: string, text_snapshot: string }
  - 200: { message: Message, suggestions: Suggestion[] }

- POST /suggestions/:id/accept
  - body: { document_id }
  - 200: { updated_text_md, applied: Suggestion }

- POST /suggestions/:id/reject
  - body: { document_id }
  - 200: { status: "rejected" }

- WS /ws/collab?document_id=:id  (Phase 2)
  - Yjs awareness + update messages for CRDT sync

## Backend Implementation Notes
- FastAPI on 0.0.0.0:8001; Motor for Mongo via MONGO_URL (from backend/.env). All routes under /api.
- Text storage is markdown/plaintext. Track-changes realized via Suggestion records with ranges. Server validates ranges against before_text to avoid drift.
- Accept flow applies patch server-side and persists updated text_md + marks suggestion accepted + emits Yjs broadcast (phase 2).

## Frontend Integration Plan
- Replace current mock suggestion shape (pattern/replaceWith) with range-based Suggestion.
- Editor computes offsets from current text_md selection, sends to /comments and /suggest.
- On /suggest response: show inline redlines; Accept/Reject calls hit POST /suggestions/:id/* and update local state.
- Versions tab writes to /versions.

## What’s Mocked Now (src/mock.js)
- initialTermSheet: sample VC term sheet text.
- sampleChat: assistant + user thread including a replace-type suggestion.
- defaultComments: seeded comment on liquidation preference.
- mockAIResponse(prompt): rule-based assistant that returns sample Suggestion(s).
- LocalStorage keys: tsc_current_text, tsc_versions, tsc_comments, tsc_chat, tsc_session_id.

## Phase 2 – GPT-4 + Yjs
- GPT-4 via Emergent LLM key: server exposes POST /suggest to call OpenAI with prompt + current text_md, returns proposed redlines; map LLM diff to Suggestion[] with ranges.
- Real-time collab: Yjs doc per Document.id; FastAPI WebSocket endpoint relays updates; Editor integrates y-websocket provider for shared text and awareness.

## Error Handling
- 4xx for validation (range out of bounds, missing params), 5xx for server errors.
- Suggestion acceptance validates that before_text matches current range or attempts minimal rebase; otherwise 409 Conflict with rebase hint.

## Security & Auth (Deferred)
- No auth for MVP. Add JWT later; restrict WS with signed tokens.

## Migration Checklist
- Create Mongo collections: documents, versions, comments, suggestions, messages, sessions (indexes on document_id, created_at).
- Wire frontend to services/api.js functions.
- Remove mock.js and move seeding to backend fixtures if needed.
