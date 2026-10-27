/**
 * authApi.ts — Typed client for the portal authentication API.
 *
 * Built on services/http.ts so every call shares the same base URL override,
 * timeout, idempotency key on writes, and error normalisation. Returns the same
 * `ApiResult<T>` envelope the sampling pages use.
 *
 * Endpoints live under AUTH_BASE (`/api/auth`), served by
 * backend/src/api/auth_routes.py.
 */

import { http, errorMessage, ApiError } from './http';
import { AUTH_BASE } from './config';

// ─── Response shape ──────────────────────────────────────────────────────────

export interface ApiResult<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  /** RFC-7807 stable error code (e.g. AUTH_REQUIRED, VALIDATION_ERROR). */
  code?: string;
  status?: number;
  /** Server correlation id for support, when supplied. */
  requestId?: string;
}

/** Normalise a thrown transport error into the ApiResult error envelope. */
function fail(error: unknown): ApiResult<never> {
  if (error instanceof ApiError) {
    return {
      success: false,
      error: error.detail,
      code: error.code,
      status: error.status,
      requestId: error.requestId,
    };
  }
  return { success: false, error: errorMessage(error) };
}

export interface ActorContext {
  actorId: string;
  /** Prototype-only stable link to the sewing operator record, when assigned. */
  operatorId?: string;
  displayName: string;
  email: string;
  role: string;
  status: string;
}

export interface SessionResult {
  accessToken: string;
  expiresIn: number;
  actor: ActorContext;
}

export interface RegistrationView {
  registration_id: string;
  full_name: string;
  email: string;
  employee_id: string;
  phone: string;
  department: string;
  status: string;
  created_at: number;
}

export interface RegisterPayload {
  full_name: string;
  email: string;
  employee_id: string;
  ktp_id: string;
  phone: string;
  department: string;
  password: string;
  consent: boolean;
}

// ─── Internals ───────────────────────────────────────────────────────────────

interface RawEnvelope {
  success?: boolean;
  message?: string;
  [key: string]: unknown;
}

async function postJson<T>(path: string, body: unknown, token?: string): Promise<ApiResult<T>> {
  try {
    const raw = await http.post<RawEnvelope>(path, { base: AUTH_BASE, body, token });
    return { success: raw?.success ?? true, data: raw as T, message: raw?.message };
  } catch (error) {
    return fail(error);
  }
}

async function getJson<T>(path: string, token?: string): Promise<ApiResult<T>> {
  try {
    const raw = await http.get<RawEnvelope>(path, { base: AUTH_BASE, token });
    return { success: raw?.success ?? true, data: raw as T };
  } catch (error) {
    return fail(error);
  }
}

// ─── Endpoints ───────────────────────────────────────────────────────────────

/** POST /register → pending registration. */
export async function register(payload: RegisterPayload): Promise<ApiResult<{ status: string }>> {
  return postJson<{ status: string }>('/register', payload);
}

/** POST /login → session (opaque access token + actor context). */
export async function login(
  identifier: string,
  password: string,
  remember = false,
): Promise<ApiResult<SessionResult>> {
  return postJson<SessionResult>('/login', { identifier, password, remember });
}

/** POST /logout → revoke the current session. */
export async function logout(token: string): Promise<ApiResult<null>> {
  return postJson<null>('/logout', {}, token);
}

/** GET /me → current actor context. */
export async function me(token: string): Promise<ApiResult<{ actor: ActorContext }>> {
  return getJson<{ actor: ActorContext }>('/me', token);
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
  );
}

/** POST /forgot-password → always a generic success (anti-enumeration). */
export async function forgotPassword(identifier: string): Promise<ApiResult<null>> {
  return postJson<null>('/forgot-password', { identifier });
}

/** POST /reset-password → set a new password using the emailed OTP. */
export async function resetPassword(
  identifier: string,
  otp: string,
  newPassword: string,
): Promise<ApiResult<null>> {
  return postJson<null>('/reset-password', {
    identifier,
    otp,
    new_password: newPassword,
  });
}

/** GET /admin/registrations → pending registrations (admin only). */
export async function listRegistrations(
  token: string,
): Promise<ApiResult<RegistrationView[]>> {
  const res = await getJson<{ data?: RegistrationView[] }>('/admin/registrations', token);
  if (!res.success || !res.data) return res as unknown as ApiResult<RegistrationView[]>;
  return { success: true, data: res.data.data ?? [] };
}

/** POST /admin/registrations/{id}/approve|reject (admin only). */
export async function decideRegistration(
  token: string,
  registrationId: string,
  decision: 'approve' | 'reject',
  role?: string,
): Promise<ApiResult<{ status: string }>> {
  const body = decision === 'approve' ? { role } : {};
  return postJson<{ status: string }>(`/admin/registrations/${registrationId}/${decision}`, body, token);
}

export const authApi = {
  register,
  login,
  logout,
  me,
  changePassword,
  forgotPassword,
  resetPassword,
  listRegistrations,
  decideRegistration,
};

export default authApi;
