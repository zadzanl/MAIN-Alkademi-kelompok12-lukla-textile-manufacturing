/**
 * http.ts — Single HTTP transport for the UHUY B2B external portal.
 *
 * One place for: base URL, request timeout (AbortController), JSON handling,
 * Idempotency-Key on writes, and error normalisation. Backend errors are
 * surfaced as a typed `ApiError` so callers never parse raw responses.
 *
 * Backend error shape: FastAPI `{ "detail": "..." }` (string or validation array).
 *
 * Known ceiling: no retry/backoff yet; add only when a real need appears.
 */
import { PORTAL_BASE } from './config';
import { buildQuery } from './query';
import { extractDetail, extractRequestId } from './problem';

export class ApiError extends Error {
  readonly status: number;
  readonly code?: string;
  readonly detail: string;
  readonly requestId?: string;

  constructor(status: number, detail: string, code?: string, requestId?: string) {
    super(detail);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
    this.code = code;
    this.requestId = requestId;
  }
}

export interface RequestOptions {
  params?: Record<string, unknown>;
  body?: unknown;
  timeoutMs?: number;
  /** Set on writes so retries of the same logical request are replay-safe. */
  idempotencyKey?: string;
  /** Override the default base URL (e.g. the portal auth API). */
  base?: string;
  /** Bearer token for authenticated calls. */
  token?: string;
}

function newIdempotencyKey(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID().replace(/-/g, '');
  }
  return `idem-${Date.now()}-${Math.random().toString(36).slice(2, 12)}`;
}

async function request<T>(
  method: 'GET' | 'POST' | 'PUT',
  path: string,
  options: RequestOptions = {},
  base: string = PORTAL_BASE,
): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), options.timeoutMs ?? 10000);

  const headers: Record<string, string> = {};
  if (options.body !== undefined) headers['Content-Type'] = 'application/json';
  if (options.token) headers['Authorization'] = `Bearer ${options.token}`;
  if (method !== 'GET') {
    headers['Idempotency-Key'] = options.idempotencyKey ?? newIdempotencyKey();
  }

  try {
    const response = await fetch(`${options.base ?? base}${path}${buildQuery(options.params)}`, {
      method,
      headers,
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
      signal: controller.signal,
    });

    const text = await response.text();
    let raw: unknown = null;
    if (text) {
      try {
        raw = JSON.parse(text);
      } catch {
        raw = text;
      }
    }

    if (!response.ok) {
      const code =
        raw && typeof raw === 'object' && typeof (raw as { code?: unknown }).code === 'string'
          ? (raw as { code: string }).code
          : undefined;
      throw new ApiError(response.status, extractDetail(raw, response.status), code, extractRequestId(raw));
    }

    return raw as T;
  } finally {
    clearTimeout(timer);
  }
}

export const http = {
  get: <T>(path: string, options?: RequestOptions) => request<T>('GET', path, options),
  post: <T>(path: string, options?: RequestOptions) => request<T>('POST', path, options),
  put: <T>(path: string, options?: RequestOptions) => request<T>('PUT', path, options),
};

/** Human-readable message for any thrown value (ApiError or network error). */
export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.detail;
  return String(error);
}
