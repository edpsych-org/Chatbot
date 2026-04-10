// Build API base URL:
// 1. Trim whitespace/newlines from env var (Vercel dashboard can add trailing \n)
// 2. Ensure /api/v1 suffix is present
// 3. Fall back to localhost for local dev
const raw = (process.env.NEXT_PUBLIC_API_URL || '').trim().replace(/\\n/g, '');
export const API_BASE = raw
  ? (raw.endsWith('/api/v1') ? raw : `${raw.replace(/\/+$/, '')}/api/v1`)
  : 'http://localhost:8000/api/v1';
export const API_DOCS_URL = API_BASE.replace('/api/v1', '/api/docs');
