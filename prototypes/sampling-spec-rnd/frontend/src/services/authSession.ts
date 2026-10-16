/**
 * authSession.ts — Single source for the current portal session.
 *
 * Holds the opaque access token + actor context in memory, mirrored to
 * `sessionStorage` so a page reload within the same tab stays logged in.
 *
 * Known ceiling: `sessionStorage` is readable by any script on the page. The
 * production design (openspec 13-authn-authz-design.md) keeps the access token
 * in memory and uses an HttpOnly refresh cookie; swap the persistence here when
 * the real issuer lands — no component needs to change.
 */

import type { ActorContext } from './authApi';

export interface AuthSession {
  token: string;
  actor: ActorContext;
}

/** Fallback session used to bypass login in development */
export const DEV_ADMIN_SESSION: AuthSession = {
  token: 'dev-admin-bypass-token',
  actor: {
    actorId: 'admin-dev-001',
    displayName: 'Administrator (Dev)',
    email: 'admin@lukla.local',
    role: 'admin',
    status: 'active',
  },
};

const STORAGE_KEY = 'portal-auth-session';

type Listener = (session: AuthSession | null) => void;
const listeners = new Set<Listener>();

function storage(): Storage | null {
  try {
    return typeof sessionStorage !== 'undefined' ? sessionStorage : null;
  } catch {
    return null;
  }
}

function load(): AuthSession | null {
  const store = storage();
  if (!store) return null;
  try {
    const raw = store.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as AuthSession;
    if (parsed && typeof parsed.token === 'string' && parsed.actor) return parsed;
    return null;
  } catch {
    return null;
  }
}

let current: AuthSession | null = load();

function emit(): void {
  listeners.forEach((listener) => listener(current));
}

export function subscribe(listener: Listener): () => void {
  listeners.add(listener);
  listener(current);
  return () => {
    listeners.delete(listener);
  };
}

export function getSession(): AuthSession | null {
  return current;
}

export function getToken(): string | null {
  return current?.token ?? null;
}

export function getActor(): ActorContext | null {
  return current?.actor ?? null;
}

export function setSession(session: AuthSession): void {
  current = session;
  storage()?.setItem(STORAGE_KEY, JSON.stringify(session));
  emit();
}

export function clearSession(): void {
  current = null;
  storage()?.removeItem(STORAGE_KEY);
  emit();
}
