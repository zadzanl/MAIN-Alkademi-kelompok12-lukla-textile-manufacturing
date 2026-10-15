import test from 'node:test';
import assert from 'node:assert/strict';
import {
  detectIdentifierKind,
  formatOtp,
  isValidEmail,
  isValidPhone,
  passwordsMatch,
  passwordStrength,
  validatePassword,
} from '../src/services/authRules.ts';
import { matchesQuery } from '../src/utils/filter.ts';

// ─── Identifier classification (external clients use email or phone) ─────────

test('detectIdentifierKind recognises email', () => {
  assert.equal(detectIdentifierKind('buyer@brand.co.id'), 'email');
});

test('detectIdentifierKind recognises phone', () => {
  assert.equal(detectIdentifierKind('0812-3456-7890'), 'phone');
});

test('detectIdentifierKind returns unknown for empty input', () => {
  assert.equal(detectIdentifierKind('   '), 'unknown');
});

// ─── Field validation ────────────────────────────────────────────────────────

test('isValidEmail accepts and rejects correctly', () => {
  assert.equal(isValidEmail('a@b.co'), true);
  assert.equal(isValidEmail('nope'), false);
});

test('isValidPhone enforces 9-15 digits', () => {
  assert.equal(isValidPhone('0812345678'), true);
  assert.equal(isValidPhone('123'), false);
});

// ─── Password rules (must mirror the backend) ────────────────────────────────

test('validatePassword requires length + letter + digit', () => {
  assert.equal(validatePassword('short1'), 'Password minimal 8 karakter.');
  assert.equal(validatePassword('onlyletters'), 'Password harus memuat huruf dan angka.');
  assert.equal(validatePassword('Rahasia123'), null);
});

test('passwordStrength scales with complexity', () => {
  assert.equal(passwordStrength('abc'), 'weak');
  assert.equal(passwordStrength('Rahasia123'), 'fair');
  assert.equal(passwordStrength('Rahasia123!Panjang'), 'strong');
});

test('passwordsMatch rejects empty and mismatched values', () => {
  assert.equal(passwordsMatch('', ''), false);
  assert.equal(passwordsMatch('a', 'b'), false);
  assert.equal(passwordsMatch('same1', 'same1'), true);
});

test('formatOtp keeps digits only and caps at 6', () => {
  assert.equal(formatOtp('12a34b56789'), '123456');
});

// ─── Shared text search ──────────────────────────────────────────────────────

test('matchesQuery is case-insensitive substring across fields', () => {
  assert.equal(matchesQuery('', 'anything'), true);
  assert.equal(matchesQuery('polo', 'Kaos Polo', 'ORD-1'), true);
  assert.equal(matchesQuery('zzz', 'Kaos Polo'), false);
});
