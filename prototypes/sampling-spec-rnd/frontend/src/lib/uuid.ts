/**
 * Tiny UUID v4 generator — avoids crypto.randomUUID() which is not available
 * in non-secure contexts (HTTP) on older Chromium builds.
 * Bug-fix #5.
 */
export function generateId(): string {
  // Use crypto.randomUUID when available (modern browsers + HTTPS)
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  // Fallback: RFC 4122 v4 UUID via Math.random
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}
