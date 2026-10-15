import test from 'node:test';
import assert from 'node:assert/strict';
import { buildQuery } from '../src/services/query.ts';

test('no params yields an empty string', () => {
  assert.equal(buildQuery(), '');
  assert.equal(buildQuery({}), '');
});

test('drops undefined, null and empty-string values', () => {
  assert.equal(buildQuery({ a: undefined, b: null, c: '' }), '');
});

test('keeps false and 0 because they are meaningful to the backend', () => {
  assert.equal(buildQuery({ is_abnormal: false }), '?is_abnormal=false');
  assert.equal(buildQuery({ cycle_time_ms: 0 }), '?cycle_time_ms=0');
});

test('URL-encodes keys and values', () => {
  assert.equal(buildQuery({ element_name: 'Jahit Kerah' }), '?element_name=Jahit+Kerah');
});

test('preserves insertion order and joins with &', () => {
  assert.equal(buildQuery({ a: 1, b: 2 }), '?a=1&b=2');
});
