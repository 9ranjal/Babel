const rawBase =
  (typeof window !== 'undefined' &&
    (import.meta as ImportMeta & { env: Record<string, string | undefined> }).env?.VITE_API_URL) ??
  (typeof window !== 'undefined' &&
    (import.meta as ImportMeta & { env: Record<string, string | undefined> }).env?.VITE_API_BASE) ??
  '';

const normalizedBase =
  typeof rawBase === 'string' && rawBase.length > 0
    ? rawBase.replace(/\/$/, '')
    : '';

export const API_BASE_URL = normalizedBase || '/api';

export const resolveApiUrl = (path: string): string => {
  const safePath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE_URL}${safePath}`;
};


