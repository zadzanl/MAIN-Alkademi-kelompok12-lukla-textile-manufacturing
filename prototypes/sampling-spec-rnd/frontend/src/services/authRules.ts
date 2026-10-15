/**
 * authRules.ts — Pure validation/formatting helpers for the portal auth forms.
 *
 * Dependency-free (no fetch, no import.meta) so the exact rules the backend
 * enforces are unit-testable under `node --test`. The backend re-validates
 * every field; these helpers exist only to give instant, consistent feedback.
 */

export type IdentifierKind = 'email' | 'employee_id' | 'ktp' | 'phone' | 'unknown';

export const PASSWORD_MIN_LENGTH = 8;

/** Trim only — the backend decides which identifier index to match. */
export function normalizeIdentifier(value: string): string {
  return value.trim();
}

/** Best-effort classification for helper text (not used for authorization). */
export function detectIdentifierKind(value: string): IdentifierKind {
  const raw = value.trim();
  if (!raw) return 'unknown';
  if (raw.includes('@')) return 'email';
  const digits = raw.replace(/\D/g, '');
  if (digits.length === 16 && digits.length === raw.replace(/\s/g, '').length) return 'ktp';
  if (/^\+?[\d\s-]{9,}$/.test(raw) && digits.length >= 9) return 'phone';
  return 'employee_id';
}

export function isValidEmail(value: string): boolean {
  return /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(value.trim());
}

export function isValidKtp(value: string): boolean {
  return /^\d{16}$/.test(value.replace(/\D/g, ''));
}

export function isValidPhone(value: string): boolean {
  const digits = value.replace(/\D/g, '');
  return digits.length >= 9 && digits.length <= 15;
}

/** Returns an error message, or null when the password is acceptable. */
export function validatePassword(password: string): string | null {
  if (password.length < PASSWORD_MIN_LENGTH) {
    return `Password minimal ${PASSWORD_MIN_LENGTH} karakter.`;
  }
  if (!/[A-Za-z]/.test(password) || !/\d/.test(password)) {
    return 'Password harus memuat huruf dan angka.';
  }
  return null;
}

export type PasswordStrength = 'weak' | 'fair' | 'strong';

export function passwordStrength(password: string): PasswordStrength {
  let score = 0;
  if (password.length >= PASSWORD_MIN_LENGTH) score += 1;
  if (password.length >= 12) score += 1;
  if (/[A-Z]/.test(password) && /[a-z]/.test(password)) score += 1;
  if (/\d/.test(password)) score += 1;
  if (/[^A-Za-z0-9]/.test(password)) score += 1;
  if (score >= 4) return 'strong';
  if (score >= 2) return 'fair';
  return 'weak';
}

export function passwordsMatch(a: string, b: string): boolean {
  return a.length > 0 && a === b;
}

/** Keep only digits and cap at 6 for the OTP input. */
export function formatOtp(value: string): string {
  return value.replace(/\D/g, '').slice(0, 6);
}

/** Mask all but the last 4 digits of a KTP/NIK. */
export function maskKtp(value: string): string {
  const digits = value.replace(/\D/g, '');
  if (digits.length <= 4) return '*'.repeat(digits.length);
  return '*'.repeat(digits.length - 4) + digits.slice(-4);
}

/** Human-readable identifier hint shown under the login field. */
export function identifierHint(kind: IdentifierKind): string {
  switch (kind) {
    case 'email':
      return 'Masuk dengan email perusahaan.';
    case 'ktp':
      return 'Masuk dengan NIK/KTP.';
    case 'phone':
      return 'Masuk dengan nomor HP.';
    case 'employee_id':
      return 'Masuk dengan nomor karyawan.';
    default:
      return 'Gunakan nomor karyawan, NIK/KTP, email, atau nomor HP.';
  }
}
