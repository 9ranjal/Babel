const rawBase =
  import.meta.env.VITE_API_URL ??
  import.meta.env.VITE_API_BASE ??
  '';

const normalizedBase =
  typeof rawBase === 'string' && rawBase.length > 0
    ? rawBase.replace(/\/$/, '')
    : '';

export const API_BASE_URL = normalizedBase;
export const API_PREFIX = normalizedBase ? '' : '/api';

export const resolveApiUrl = (path: string): string => {
  const safePath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE_URL}${API_PREFIX}${safePath}`;
};


