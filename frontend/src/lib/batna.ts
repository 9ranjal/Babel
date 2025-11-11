// Helper functions for ZOPA analysis display

export type Leverage = {
  investor: number;
  founder: number;
};

export type PostureColor = 'green' | 'blue' | 'red' | 'gray';

export function getPostureColor(posture: string | null): PostureColor {
  switch (posture) {
    case 'founder_friendly':
      return 'green';
    case 'market':
      return 'blue';
    case 'investor_friendly':
      return 'red';
    default:
      return 'gray';
  }
}

export function formatLeverage(leverage: Leverage | null): string {
  if (!leverage) return 'Default (0.6/0.4)';
  return `Investor: ${(leverage.investor * 100).toFixed(0)}%, Founder: ${(leverage.founder * 100).toFixed(0)}%`;
}

export function formatBandScore(score: number | null): string {
  if (score === null) return '—';
  return score.toFixed(3);
}

export function getPostureDisplayName(posture: string | null): string {
  switch (posture) {
    case 'founder_friendly':
      return 'Founder Friendly';
    case 'market':
      return 'Market';
    case 'investor_friendly':
      return 'Investor Friendly';
    default:
      return 'Unknown';
  }
}

export const DEFAULT_LEVERAGE: Leverage = { investor: 0.6, founder: 0.4 };
