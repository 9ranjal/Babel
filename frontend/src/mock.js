// Mock data and helpers for Term Sheet Copilot (frontend-only)
// NOTE: This is MOCKED data. No backend or AI yet. Uses localStorage for versions & comments.

export const initialTermSheet = `
TERM SHEET — SEED PREFERRED FINANCING (SAMPLE)

1. Financing Amount: $2,000,000 in Seed Preferred Stock (the "Financing").
2. Valuation Cap: $10,000,000 pre-money.
3. Discount: 20% discount on next equity financing.
4. Liquidation Preference: 1x non-participating.
5. Pro Rata Rights: Investors have pro rata rights in next round.
6. Board: 1 common, 1 investor, 1 independent.
7. Information Rights: Standard quarterly and annual reporting.
8. Option Pool: Post-money option pool of 10%.
9. Use of Proceeds: Working capital and product development.
10. Closing: Subject to due diligence and definitive agreements.
`;

export const sampleChat = [
  {
    id: "m1",
    role: "assistant",
    content:
      "Hi! I’m your Term Sheet Copilot. Paste a clause or ask me to redline any section. I can suggest edits and explain legal terms in plain English.",
    ts: Date.now() - 1000 * 60 * 5,
  },
  {
    id: "m2",
    role: "user",
    content: "Can we increase the valuation cap?",
    ts: Date.now() - 1000 * 60 * 4,
  },
  {
    id: "m3",
    role: "assistant",
    content:
      "Suggestion: Raise the Valuation Cap from $10,000,000 to $12,000,000. Rationale: aligns with market comps and your traction.",
    suggestion: {
      id: "s1",
      type: "replace",
      pattern: "Valuation Cap: $10,000,000",
      replaceWith: "Valuation Cap: $12,000,000",
      rationale: "Market comps for seed AI infra suggest $12–15M pre-money.",
      clauseHint: "2. Valuation Cap",
    },
    ts: Date.now() - 1000 * 60 * 4 + 15,
  },
];

export function mockAIResponse(prompt) {
  // Super simple rule-based mock for now
  const lower = prompt.toLowerCase();
  if (lower.includes("valuation") && (lower.includes("increase") || lower.includes("raise"))) {
    return {
      role: "assistant",
      content:
        "Proposed redline: Increase Valuation Cap from $10,000,000 to $12,000,000. This may reduce investor allocation but improves founder dilution.",
      suggestion: {
        id: `s-${Date.now()}`,
        type: "replace",
        pattern: "Valuation Cap: $10,000,000",
        replaceWith: "Valuation Cap: $12,000,000",
        rationale: "Reflects traction and comparable rounds.",
        clauseHint: "2. Valuation Cap",
      },
    };
  }
  if (lower.includes("explain") && (lower.includes("liquidation") || lower.includes("preference"))) {
    return {
      role: "assistant",
      content:
        "Liquidation Preference (1x non-participating) means investors get their investment back first, then remaining proceeds go to common shareholders. Non-participating = no double dip.",
    };
  }
  if (lower.includes("redline") && lower.includes("discount")) {
    return {
      role: "assistant",
      content:
        "Proposed redline: Reduce Discount from 20% to 15% to balance investor upside and signaling.",
      suggestion: {
        id: `s-${Date.now()}`,
        type: "replace",
        pattern: "Discount: 20%",
        replaceWith: "Discount: 15%",
        rationale: "Still market standard while reducing dilution at Series A.",
        clauseHint: "3. Discount",
      },
    };
  }
  // default friendly response
  return {
    role: "assistant",
    content:
      "I can redline any clause. Try: ‘raise valuation cap to $12M’ or ‘explain liquidation preference’.",
  };
}

export const defaultComments = [
  {
    id: "c1",
    snippet: "1x non-participating",
    note: "Confirm investor expects non-participating, not participating preferred.",
    anchorPattern: "Liquidation Preference: 1x non-participating",
    ts: Date.now() - 1000 * 60 * 3,
  },
];

export const STORAGE_KEYS = {
  versions: "tsc_versions",
  current: "tsc_current_text",
  comments: "tsc_comments",
  chat: "tsc_chat",
  session: "tsc_session_id",
};

export function getSessionId() {
  let id = localStorage.getItem(STORAGE_KEYS.session);
  if (!id) {
    id = `sess_${Date.now()}_${Math.random().toString(16).slice(2)}`;
    localStorage.setItem(STORAGE_KEYS.session, id);
  }
  return id;
}

export function loadInitialState() {
  const existingText = localStorage.getItem(STORAGE_KEYS.current);
  const existingVersions = JSON.parse(localStorage.getItem(STORAGE_KEYS.versions) || "[]");
  const existingComments = JSON.parse(localStorage.getItem(STORAGE_KEYS.comments) || "null");
  const existingChat = JSON.parse(localStorage.getItem(STORAGE_KEYS.chat) || "null");
  return {
    text: existingText || initialTermSheet,
    versions: existingVersions,
    comments: existingComments || defaultComments,
    chat: existingChat || sampleChat,
  };
}

export function persistState({ text, versions, comments, chat }) {
  if (typeof text === "string") localStorage.setItem(STORAGE_KEYS.current, text);
  if (Array.isArray(versions)) localStorage.setItem(STORAGE_KEYS.versions, JSON.stringify(versions));
  if (Array.isArray(comments)) localStorage.setItem(STORAGE_KEYS.comments, JSON.stringify(comments));
  if (Array.isArray(chat)) localStorage.setItem(STORAGE_KEYS.chat, JSON.stringify(chat));
}
