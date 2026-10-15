import test from 'node:test';
import assert from 'node:assert/strict';
import { matchesQuery } from '../src/utils/filter.ts';

test('blank or whitespace query matches everything', () => {
  assert.equal(matchesQuery('', 'Jahit Baju'), true);
  assert.equal(matchesQuery('   ', 'Jahit Baju'), true);
});

test('case-insensitive substring match on any field', () => {
  assert.equal(matchesQuery('jahit', 'Jahit Baju', 'PROC-001'), true);
  assert.equal(matchesQuery('proc-001', 'Jahit Baju', 'PROC-001'), true);
  assert.equal(matchesQuery('  SPEC ', undefined, 'SPEC-009'), true);
});

test('non-matching query returns false', () => {
  assert.equal(matchesQuery('kancing', 'Jahit Baju', 'PROC-001'), false);
});

test('undefined/null fields are ignored without throwing', () => {
  assert.equal(matchesQuery('x', undefined, null), false);
});
