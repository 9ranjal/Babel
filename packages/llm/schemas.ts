export type NormalizedClause = {
  clause_key: string;
  attributes: { value: any };
  confidence: number;
};

export type BatnaAdvice = {
  posture: "founder_friendly" | "market" | "investor_friendly";
  band_name: string | null;
  band_score: number | null;
  rationale: string[];
  recommendation: string;
  trades: string[];
  redraft?: string | null;
};
