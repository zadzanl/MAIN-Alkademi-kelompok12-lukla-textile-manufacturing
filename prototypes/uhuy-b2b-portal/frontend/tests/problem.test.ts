import test from 'node:test';
import assert from 'node:assert/strict';
import { extractDetail } from '../src/services/problem.ts';

test('FastAPI HTTPException detail string', () => {
  assert.equal(extractDetail({ detail: 'Study not found' }, 400), 'Study not found');
});

test('FastAPI validation array is flattened to readable text', () => {
  const body = { detail: [{ loc: ['query', 'cycle_time_ms'], msg: 'Field required' }] };
  assert.equal(extractDetail(body, 422), 'query.cycle_time_ms: Field required');
});

test('RFC 7807 problem uses detail, falls back to title', () => {
  assert.equal(extractDetail({ code: 'INVALID_STATE', detail: 'bad state' }, 409), 'bad state');
  assert.equal(extractDetail({ title: 'Conflict' }, 409), 'Conflict');
});

test('plain text body is returned as-is', () => {
  assert.equal(extractDetail('gateway timeout', 504), 'gateway timeout');
});

test('unknown shape falls back to HTTP status', () => {
  assert.equal(extractDetail(null, 500), 'HTTP 500');
  assert.equal(extractDetail({}, 503), 'HTTP 503');
});
