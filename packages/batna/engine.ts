export type Leverage = { investor: number; founder: number };

export type Band = {
  name: string;
  range?: [number, number];
  enum_match?: string;
  predicate?: string; // evaluated in backend code if needed
  founder_score: number;
  investor_score: number;
  rationale?: string;
};

export function compositeScore(b: Band, lev: Leverage) {
  return (b.investor_score || 0) * lev.investor + (b.founder_score || 0) * lev.founder;
}

export function pickBand(bands: Band[], attrs: any, lev: Leverage): Band | null {
    const v = attrs?.value;
  const matches = bands.filter(b => {
    if (b.range && typeof v === "number") {
    return v >= b.range[0] && v <= b.range[1];
    }
    if (b.enum_match && typeof v === "string") {
      return v === b.enum_match;
    }
    if (!b.range && !b.enum_match) {
      return true; // predicate-only band; let backend refine if needed
    }
    return false;
  });

  if (matches.length === 0) return null;

  matches.sort((a, b) => compositeScore(b, lev) - compositeScore(a, lev));

  const top = matches.filter(m => m.name.toLowerCase() === "market")[0] || matches[0];

  return top;
}

export const DEFAULT_LEVERAGE: Leverage = { investor: 0.6, founder: 0.4 };


