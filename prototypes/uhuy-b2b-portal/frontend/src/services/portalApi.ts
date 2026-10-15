/**
 * portalApi.ts — Typed client for the UHUY B2B external-portal API.
 *
 * Built on services/http.ts so every call shares the same base-URL override,
 * timeout, idempotency key on writes, and error normalisation. Returns a uniform
 * `ApiResult<T>` envelope so pages never parse raw responses.
 *
 * Endpoints live under PORTAL_BASE (`/api/portal`) and PORTAL_AUTH_BASE
 * (`/api/portal/auth`), served by the dedicated external-portal backend (8010).
 */

import { http, errorMessage } from './http';
import { PORTAL_BASE, PORTAL_AUTH_BASE } from './config';
import type {
  ActorContext,
  Order,
  OrderRequestPayload,
  PortalRequest,
  PortalSummary,
  RegisterPayload,
  SampleRequestPayload,
  SessionResult,
  StockLot,
} from '../types/portal';

// ─── Response envelope ───────────────────────────────────────────────────────

export interface ApiResult<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

interface RawEnvelope {
  success?: boolean;
  message?: string;
  [key: string]: unknown;
}

async function getJson<T>(path: string, token: string): Promise<ApiResult<T>> {
  try {
    const raw = await http.get<RawEnvelope>(path, { base: PORTAL_BASE, token });
    return { success: raw?.success ?? true, data: raw as T, message: raw?.message };
  } catch (error) {
    return { success: false, error: errorMessage(error) };
  }
}

async function postJson<T>(
  path: string,
  body: unknown,
  token?: string,
  base: string = PORTAL_BASE,
): Promise<ApiResult<T>> {
  try {
    const raw = await http.post<RawEnvelope>(path, { base, body, token });
    return { success: raw?.success ?? true, data: raw as T, message: raw?.message };
  } catch (error) {
    return { success: false, error: errorMessage(error) };
  }
}

function unwrapList<T>(res: ApiResult<{ data?: T[] }>): ApiResult<T[]> {
  if (!res.success || !res.data) return { success: res.success, error: res.error };
  return { success: true, data: res.data.data ?? [] };
}

// ─── Auth (external client) ──────────────────────────────────────────────────

/** POST /register → pending client registration. */
export async function register(
  payload: RegisterPayload,
): Promise<ApiResult<{ status: string; client_id: string }>> {
  return postJson<{ status: string; client_id: string }>(
    '/register',
    payload,
    undefined,
    PORTAL_AUTH_BASE,
  );
}

/** POST /login → session (opaque access token + client actor context). */
export async function login(
  identifier: string,
  password: string,
  remember = false,
): Promise<ApiResult<SessionResult>> {
  return postJson<SessionResult>(
    '/login',
    { identifier, password, remember },
    undefined,
    PORTAL_AUTH_BASE,
  );
}

/** POST /logout → revoke the current session. */
export async function logout(token: string): Promise<ApiResult<null>> {
  return postJson<null>('/logout', {}, token, PORTAL_AUTH_BASE);
}

/** GET /me → current client actor context. */
export async function me(token: string): Promise<ApiResult<{ actor: ActorContext }>> {
  try {
    const raw = await http.get<RawEnvelope>('/me', { base: PORTAL_AUTH_BASE, token });
    return { success: raw?.success ?? true, data: raw as { actor: ActorContext } };
  } catch (error) {
    return { success: false, error: errorMessage(error) };
  }
}

/** POST /change-password → update password (session is revoked server-side). */
export async function changePassword(
  token: string,
  currentPassword: string,
  newPassword: string,
): Promise<ApiResult<null>> {
  return postJson<null>(
    '/change-password',
    { current_password: currentPassword, new_password: newPassword },
    token,
    PORTAL_AUTH_BASE,
  );
}

/** POST /forgot-password → always a generic success (anti-enumeration). */
export async function forgotPassword(identifier: string): Promise<ApiResult<null>> {
  return postJson<null>('/forgot-password', { identifier }, undefined, PORTAL_AUTH_BASE);
}

/** POST /reset-password → set a new password using the emailed OTP. */
export async function resetPassword(
  identifier: string,
  otp: string,
  newPassword: string,
): Promise<ApiResult<null>> {
  return postJson<null>(
    '/reset-password',
    { identifier, otp, new_password: newPassword },
    undefined,
    PORTAL_AUTH_BASE,
  );
}

// ─── Health ──────────────────────────────────────────────────────────────────

/** GET /health → true when the external-portal backend is reachable. */
export async function health(): Promise<boolean> {
  try {
    const raw = await http.get<RawEnvelope>('/health', { base: PORTAL_BASE, timeoutMs: 5000 });
    return raw?.status === 'healthy';
  } catch {
    return false;
  }
}

// ─── Client-scoped data ──────────────────────────────────────────────────────

/** GET /summary → KPI for the signed-in client. */
export async function getSummary(token: string): Promise<ApiResult<{ summary: PortalSummary }>> {
  return getJson<{ summary: PortalSummary }>('/summary', token);
}

/** GET /orders → own orders only (server-scoped by client_id). */
export async function listOrders(token: string): Promise<ApiResult<Order[]>> {
  return unwrapList<Order>(await getJson<{ data?: Order[] }>('/orders', token));
}

/** GET /orders/{id} → own order detail (404 for another client's id). */
export async function getOrder(token: string, orderId: string): Promise<ApiResult<{ data: Order }>> {
  return getJson<{ data: Order }>(`/orders/${encodeURIComponent(orderId)}`, token);
}

/** GET /stock → own consigned material only. */
export async function listStock(token: string): Promise<ApiResult<StockLot[]>> {
  return unwrapList<StockLot>(await getJson<{ data?: StockLot[] }>('/stock', token));
}

/** GET /requests → own submitted requests only. */
export async function listRequests(token: string): Promise<ApiResult<PortalRequest[]>> {
  return unwrapList<PortalRequest>(await getJson<{ data?: PortalRequest[] }>('/requests', token));
}

/** POST /requests/order → submit a new production order request. */
export async function createOrderRequest(
  token: string,
  payload: OrderRequestPayload,
): Promise<ApiResult<{ request_id: string; status: string }>> {
  return postJson<{ request_id: string; status: string }>('/requests/order', payload, token);
}

/** POST /requests/sample → submit a new design/sample request. */
export async function createSampleRequest(
  token: string,
  payload: SampleRequestPayload,
): Promise<ApiResult<{ request_id: string; status: string }>> {
  return postJson<{ request_id: string; status: string }>('/requests/sample', payload, token);
}

export const portalApi = {
  health,
  register,
  login,
  logout,
  me,
  changePassword,
  forgotPassword,
  resetPassword,
  getSummary,
  listOrders,
  getOrder,
  listStock,
  listRequests,
  createOrderRequest,
  createSampleRequest,
};

export default portalApi;
