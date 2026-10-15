/**
 * Pure-rule tests for the portal auth form helpers (services/authRules.ts).
 *
 * These pin the client-side rules that mirror the backend validation in
 * backend/src/api/auth_routes.py, so the two cannot drift silently.
 */

import test from 'node:test';
import assert from 'node:assert/strict';

import {
  detectIdentifierKind,
  formatOtp,
  isValidEmail,
  isValidKtp,
  isValidPhone,
  maskKtp,
  passwordStrength,
  passwordsMatch,
  validatePassword,
} from '../src/services/authRules.ts';

test('identifier kinds are detected for the four login methods', () => {
  assert.equal(detectIdentifierKind('budi@luka.local'), 'email');
  assert.equal(detectIdentifierKind('EMP-001'), 'employee_id');
  assert.equal(detectIdentifierKind('3201010101010001'), 'ktp');
  assert.equal(detectIdentifierKind('081234567890'), 'phone');
  assert.equal(detectIdentifierKind('   '), 'unknown');
});

test('email validation matches the backend regex shape', () => {
  assert.equal(isValidEmail('a@b.co'), true);
  assert.equal(isValidEmail('no-at-sign'), false);
  assert.equal(isValidEmail('a@b'), false);
});

test('KTP validation requires exactly 16 digits', () => {
  assert.equal(isValidKtp('3201010101010001'), true);
  assert.equal(isValidKtp('3201 0101 0101 0001'), true);
  assert.equal(isValidKtp('12345'), false);
});

test('phone validation accepts 9–15 digits', () => {
  assert.equal(isValidPhone('081234567890'), true);
  assert.equal(isValidPhone('+62 812-3456-7890'), true);
  assert.equal(isValidPhone('123'), false);
});

test('password policy requires 8+ chars with a letter and a digit', () => {
  assert.match(validatePassword('short1') ?? '', /minimal 8/);
  assert.match(validatePassword('onlyletters') ?? '', /huruf dan angka/);
  assert.equal(validatePassword('Rahasia123'), null);
});

test('password strength escalates with length and character mix', () => {
  assert.equal(passwordStrength('abc'), 'weak');
  assert.equal(passwordStrength('abcdefg1'), 'fair');
  assert.equal(passwordStrength('Rahasia123!Panjang'), 'strong');
});

test('passwordsMatch rejects empty and mismatched values', () => {
  assert.equal(passwordsMatch('', ''), false);
  assert.equal(passwordsMatch('abc12345', 'abc12345'), true);
  assert.equal(passwordsMatch('abc12345', 'abc12346'), false);
});

test('formatOtp keeps only digits and caps at six', () => {
  assert.equal(formatOtp('12a3 4567'), '123456');
  assert.equal(formatOtp('1234567890'), '123456');
});

test('maskKtp hides all but the last four digits', () => {
  assert.equal(maskKtp('3201010101010001'), '************0001');
  assert.equal(maskKtp('123'), '***');
});
