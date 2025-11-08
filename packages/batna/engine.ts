export type Leverage = { investor: number; founder: number };

export function pickBand(bands: any[], attrs: any, lev: Leverage) {
  const within = (b: any) => {
    if (!b.range) return true;
    const v = attrs?.value;
    if (typeof v !== "number") return true;
    return v >= b.range[0] && v <= b.range[1];
  };
  const scored = bands
    .filter(within)
    .map((b) => ({ b, s: (b.investor_score || 0) * lev.investor + (b.founder_score || 0) * lev.founder }))
    .sort((a, b) => b.s - a.s);
  return scored[0]?.b || null;
}


